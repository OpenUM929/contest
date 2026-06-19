from app.services.claude import generate_text
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from pathlib import Path
import uuid
import logging

from app.models.models import SurveyResponse, Conversation, Essay, EssayContributor, WeeklyTopic
from app.services.mbti import build_option_pole_map, tally_poles, summarize, short_label

logger = logging.getLogger("ium.essay")

PROMPT_DIR = Path(__file__).parent.parent / "prompts"

# v3: 장르별 작가 프롬프트 (MBTI 캐릭터화 + 참여자 주인공화). public_data.generate_topic_question 과 동일하게
# prompts 디렉토리의 텍스트 템플릿을 로드하여 사용한다.
GENRE_PROMPT_FILES = {
    "essay": "essay_author_v1.txt",
    "poem": "poem_author_v1.txt",
    "novel": "novel_author_v1.txt",
}

ESSAY_PROMPT_V0 = """\
아래는 '{topic}'을 주제로 여러 사람이 AI와 나눈 대화 기록입니다.
각자의 기억과 감정이 담겨 있습니다.

이 대화들을 하나로 엮어 짧은 수필(800~1200자)을 써주세요.

조건:
- 특정 인물을 지칭하지 말 것 (모두 익명 처리)
- 서로 다른 세대의 기억이 자연스럽게 섞이도록
- 따뜻하고 문학적인 문체
- 마지막 문장은 희망이나 연결감으로 마무리
- 맨 첫 줄에 제목(20자 이내)을 "[제목: ...]" 형식으로 작성

대화 기록:
{conversations}
"""

ESSAY_PROMPT_V1 = """\
[수필 작가·상담 전문가 공동 설계 프롬프트 v1.1 — 안개비처럼]

당신은 세대 간 이야기를 엮는 작가입니다.
아래 대화 기록은 고독한 이들이 문화적 기억을 통해 나눈 진솔한 이야기입니다.

[철학 — 안개비처럼]
이야기는 주제에서 시작하지만, 사람의 삶으로 스스로 흘러가야 합니다.
강제로 감동을 요구하지 않고, 이야기가 머물 수 있는 공간을 만드세요.
"가장 기억에 남는", "가장 감동적인" 등 최고급 표현은 사용하지 마세요.

창작 원칙:
1. 각 목소리는 독립적으로 존중받아야 합니다 — 통합하되 소거하지 마세요
2. 특정 개인을 지칭하는 표현 금지 (모든 주어를 '우리', '어떤 이', '누군가'로)
3. 감정의 과장 금지 — 담담하게 기술하되 울림이 있도록
4. 세대 간 거리를 좁히는 공통 감각을 찾아 연결
5. 마무리는 다음 주 대화에 대한 기대감으로 끝내주세요

심리적 안전 원칙:
- 트라우마를 자극할 수 있는 직접적 표현 회피
- 상실·외로움은 인정하되 절망으로 끝내지 않음
- 읽는 이가 자신의 이야기를 발견할 수 있도록 여백 유지

분량: 800~1200자
맨 첫 줄: "[제목: ...]" 형식으로 제목(20자 이내) 작성

대화 기록:
{conversations}
"""

ESSAY_PROMPT_V2 = """\
[수필 작가·상담 전문가 공동 설계 프롬프트 v2.0 — 개성 도출]

당신은 세대 간 이야기를 엮는 작가입니다.
아래는 각 참여자의 **선택형 응답**과 **서술형 이야기**입니다.

[참여자 분석 지침]
- 선택형 응답: 참여자의 경향성, 가치관, 기억의 방향을 보여줍니다.
- 서술형 이야기: 그 경향성 뒤에 숨은 구체적인 삶을 보여줍니다.
- 두 가지를 결합하여 "이 사람은 이런 사람이다"를 추론하되,
  직접 판단하지 말고 이야기에 스며들게 하세요.

[예시]
- 선택: "예 (시장에 가본 적 있다)" + 서술: "어머니가 생선을 손질해 주셨다"
  → 해석: "어떤 이는 시장의 생선을 통해 손맛과 정성을 기억한다"
- 선택: "아니오" + 서술: "나는 온라인으로만 산다"
  → 해석: "또 다른 이는 화면 속에서 세상을 만지며 편리함을 안다"

[창작 원칙]
1. 각 목소리는 독립적으로 존중받아야 합니다 — 통합하되 소거하지 마세요
2. 특정 개인을 지칭하는 표현 금지 (모든 주어를 '우리', '어떤 이', '누군가'로)
3. 감정의 과장 금지 — 담담하게 기술하되 울림이 있도록
4. 세대 간 거리를 좁히는 공통 감각을 찾아 연결
5. 마무리는 다음 주 대화에 대한 기대감으로 끝내주세요

심리적 안전 원칙:
- 트라우마를 자극할 수 있는 직접적 표현 회피
- 상실·외로움은 인정하되 절망으로 끝내지 않음
- 읽는 이가 자신의 이야기를 발견할 수 있도록 여백 유지

분량: 800~1200자
맨 첫 줄: "[제목: ...]" 형식으로 제목(20자 이내) 작성

참여자 기록:
{contributions}
"""


def _select_prompt(version: str, content_type: str = "essay") -> str:
    type_instruction = {
        "essay": "수필(800~1200자)",
        "poem": "자유시(20~40행, 단정한 행 나눔, 감정과 이미지 중심)",
        "novel": "단편소설(1000~1500자, 1~2인칭 시점, 간결한 대화 포함)",
    }.get(content_type, "수필(800~1200자)")

    base = ESSAY_PROMPT_V2 if version == "v2" else (ESSAY_PROMPT_V1 if version == "v1" else ESSAY_PROMPT_V0)

    type_suffix = (
        "\n\n[출력 형식]\n"
        f"- 장르: {type_instruction}\n"
        "- 맨 첫 줄: '[제목: ...]' 형식으로 제목(20자 이내) 작성\n"
    )
    return base + type_suffix


async def _fetch_survey_responses(
    db: AsyncSession, topic_id: str
) -> list[tuple[str, str | None, str | None]]:
    """survey_responses 전체 조회 — (user_id, narrative_text, selected_option_label) 반환
    선택형 응답(selected_option_label)과 서술형 응답(narrative_text)을 모두 포함.
    """
    result = await db.execute(
        select(
            SurveyResponse.user_id,
            SurveyResponse.narrative_text,
            SurveyResponse.selected_option_label,
        )
        .where(SurveyResponse.topic_id == uuid.UUID(topic_id))
        .order_by(SurveyResponse.responded_at)
    )
    return [
        (str(row[0]), row[1], row[2])
        for row in result.all()
        if row[1] or row[2]  # 둘 중 하나라도 있으면 포함
    ]


async def _fetch_survey_messages(db: AsyncSession, topic_id: str) -> list[tuple[str, str]]:
    """survey_responses.narrative_text 우선 조회 — (user_id, text) 반환 (하위호환)"""
    result = await db.execute(
        select(SurveyResponse.user_id, SurveyResponse.narrative_text)
        .where(
            SurveyResponse.topic_id == uuid.UUID(topic_id),
            SurveyResponse.narrative_text != None,
        )
        .order_by(SurveyResponse.responded_at)
    )
    return [(str(row[0]), row[1]) for row in result.all() if row[1]]


async def _fetch_conversation_messages(db: AsyncSession, topic_id: str) -> list[tuple[str, str]]:
    """conversations(role='user') 폴백 조회 — (user_id, text) 반환"""
    result = await db.execute(
        select(Conversation.user_id, Conversation.content)
        .where(
            Conversation.role == "user",
            Conversation.topic_id == uuid.UUID(topic_id),
        )
        .order_by(Conversation.created_at)
    )
    return [(str(row[0]), row[1]) for row in result.all() if row[1]]


def _load_genre_prompt(content_type: str) -> str:
    """v3 장르별 작가 프롬프트 로드. 알 수 없는 유형은 수필로 폴백."""
    filename = GENRE_PROMPT_FILES.get(content_type, GENRE_PROMPT_FILES["essay"])
    return (PROMPT_DIR / filename).read_text(encoding="utf-8")


async def _fetch_survey_responses_full(
    db: AsyncSession, topic_id: str
) -> list[tuple[str, str | None, str | None, str | None, str | None]]:
    """v3용 전체 응답 조회 — (user_id, question_id, narrative, selected_option_id, selected_option_label).
    선택형 선택지 ID(question_id+selected_option_id)까지 가져와 MBTI 매핑에 사용한다.
    """
    result = await db.execute(
        select(
            SurveyResponse.user_id,
            SurveyResponse.question_id,
            SurveyResponse.narrative_text,
            SurveyResponse.selected_option_id,
            SurveyResponse.selected_option_label,
        )
        .where(SurveyResponse.topic_id == uuid.UUID(topic_id))
        .order_by(SurveyResponse.responded_at)
    )
    return [
        (str(r[0]), r[1], r[2], r[3], r[4])
        for r in result.all()
        if (r[2] or r[4])  # 서술형 또는 선택형 라벨 중 하나라도 있으면 포함
    ]


def _build_contributions_block(
    rows: list[tuple[str, str | None, str | None, str | None, str | None]],
    pole_map: dict[tuple[str, str], str],
) -> str:
    """참여자별 응답을 '참여자 N' 블록으로 묶는다 (수량 제한 없음).
    rows: (user_id, question_id, narrative, selected_option_id, selected_option_label)
    pole_map가 있으면 선택형 응답으로 추정한 MBTI 성향을 블록 머리에 덧붙인다.
    서술형이 비어 있어도 선택형·추정 성향만으로 블록을 만든다.
    """
    user_data: dict[str, dict] = {}
    order: list[str] = []
    for uid, q_id, narr, opt_id, opt_label in rows:
        if uid not in user_data:
            user_data[uid] = {"choices": [], "narratives": [], "votes": []}
            order.append(uid)
        d = user_data[uid]
        if opt_label:
            d["choices"].append(opt_label)
        if q_id and opt_id:
            d["votes"].append((q_id, opt_id))
        if narr and narr.strip():
            d["narratives"].append(narr.strip())

    blocks: list[str] = []
    for idx, uid in enumerate(order, start=1):
        d = user_data[uid]
        head = f"[참여자 {idx}]"
        if pole_map and d["votes"]:
            label = short_label(summarize(tally_poles(d["votes"], pole_map)))
            if label:
                head = f"[참여자 {idx}] (추정 성향: {label})"
        parts = [head]
        if d["choices"]:
            parts.append("· 선택형 응답: " + ", ".join(d["choices"]))
        if d["narratives"]:
            parts.append("· 서술형 응답: " + " / ".join(n[:300] for n in d["narratives"]))
        else:
            parts.append("· 서술형 응답: (없음 — 주제 설명과 선택형·추정 성향으로 인물을 그려 주세요)")
        blocks.append("\n".join(parts))
    return "\n\n".join(blocks)


async def generate_essay(
    topic_id: str,
    topic_title: str,
    db: AsyncSession,
    prompt_version: str = "v1",
    content_type: str = "essay",
    reference_titles: str | None = None,
) -> tuple[str, str, int, dict[str, int]]:
    """
    (title, content, contributor_cnt, contributor_stats) 반환
    contributor_stats: {user_id: message_count}
    데이터 소스 우선순위:
    1. survey_responses (선택형 + 서술형, v2)
    2. survey_responses.narrative_text (v1/v0 하위호환)
    3. conversations(role='user') (구버전 데이터 하위호환)

    prompt_version == "v3": 장르별 작가 프롬프트 사용. 수량 제한(최소 5건/최대 20건) 없이
    모든 설문 응답을 혼합하고, 참여자별 MBTI를 유추해 각자가 주인공이 되도록 작품을 생성한다.
    reference_titles: 복지사가 참고로 입력한 작품 제목(들).
    """
    if prompt_version == "v3":
        # 주제 메타 로드: 설명(지문 없어도 글의 토대) + 발행된 선택지(MBTI 매핑용)
        topic_row = (
            await db.execute(select(WeeklyTopic).where(WeeklyTopic.id == uuid.UUID(topic_id)))
        ).scalar_one_or_none()
        description = (topic_row.description if topic_row else None) or ""
        pole_map = build_option_pole_map(topic_row.choices if topic_row else None)

        rows = await _fetch_survey_responses_full(db, topic_id)
        if not rows:
            # 설문 응답이 없으면 구버전 대화 데이터로 폴백 (선택형/MBTI 없음)
            rows = [
                (uid, None, text, None, None)
                for uid, text in await _fetch_conversation_messages(db, topic_id)
            ]
        if not rows:
            raise ValueError("작품 생성을 위한 설문 응답이 없습니다.")

        contributor_stats: dict[str, int] = {}
        for row in rows:
            uid = row[0]
            contributor_stats[uid] = contributor_stats.get(uid, 0) + 1
        contributor_cnt = len(contributor_stats)

        contributions = _build_contributions_block(rows, pole_map)
        ref_block = reference_titles.strip() if reference_titles and reference_titles.strip() else "(참고 작품 없음)"
        prompt = _load_genre_prompt(content_type).format(
            topic=topic_title,
            topic_description=description or "(설명 없음)",
            contributions=contributions,
            reference_titles=ref_block,
        )
        raw = await generate_text(prompt, max_tokens=3000)
        lines = raw.strip().splitlines()
        title = topic_title
        content_start = 0
        if lines and lines[0].startswith("[제목:"):
            title = lines[0].replace("[제목:", "").replace("]", "").strip()
            content_start = 1
        content = "\n".join(lines[content_start:]).strip()
        if not content:
            raise ValueError("AI 응답이 비어 작품 생성에 실패했습니다. 잠시 후 다시 시도해 주세요.")
        return title, content, contributor_cnt, contributor_stats

    # v2: 선택형 + 서술형 모두 수집 / v1·v0: 서술형만 (3-튜플로 통일)
    if prompt_version == "v2":
        rows = await _fetch_survey_responses(db, topic_id)
    else:
        rows = [(uid, text, None) for uid, text in await _fetch_survey_messages(db, topic_id)]

    # 부족하면 conversations 폴백
    if len(rows) < 5:
        conv_rows = await _fetch_conversation_messages(db, topic_id)
        for user_id, text in conv_rows:
            rows.append((user_id, text, None))

    if len(rows) < 5:
        raise ValueError("수필 생성을 위해 최소 5건의 대화가 필요합니다.")

    # 기여자별 메시지 수 집계
    contributor_stats: dict[str, int] = {}
    for user_id, _, _ in rows:
        contributor_stats[user_id] = contributor_stats.get(user_id, 0) + 1
    contributor_cnt = len(contributor_stats)

    # 프롬프트 구성
    if prompt_version == "v2":
        # 사용자별 응답 그룹핑 (선택형 + 서술형 결합)
        user_entries: dict[str, list[str]] = {}
        for user_id, narr, choice in rows:
            if user_id not in user_entries:
                user_entries[user_id] = []
            parts = []
            if choice:
                parts.append(f"선택: {choice}")
            if narr:
                parts.append(f"서술: {narr[:200]}")
            user_entries[user_id].append(" / ".join(parts))

        contribution_lines = []
        for user_id, items in user_entries.items():
            contribution_lines.append(f"- 참여자: {' / '.join(items)}")
        prompt = _select_prompt(prompt_version, content_type).format(
            contributions="\n".join(contribution_lines[:20]),
        )
    else:
        messages = [text for _, text, _ in rows if text]
        summaries = [f"- {m[:200]}" for m in messages[:20]]
        prompt = _select_prompt(prompt_version, content_type).format(
            topic=topic_title,
            conversations="\n".join(summaries),
        )

    raw = await generate_text(prompt, max_tokens=1500)
    lines = raw.strip().splitlines()

    title = topic_title
    content_start = 0
    if lines and lines[0].startswith("[제목:"):
        title = lines[0].replace("[제목:", "").replace("]", "").strip()
        content_start = 1

    content = "\n".join(lines[content_start:]).strip()
    if not content:
        raise ValueError("AI 응답이 비어 작품 생성에 실패했습니다. 잠시 후 다시 시도해 주세요.")
    return title, content, contributor_cnt, contributor_stats


async def auto_generate_weekly_essay() -> None:
    """일요일 23:00 자동 실행 — 이번 주 활성 주제로 수필 생성 및 저장 (D-3)"""
    from app.database import AsyncSessionLocal
    from app.services.public_data import get_active_topic

    async with AsyncSessionLocal() as db:
        try:
            topic = await get_active_topic(db)
            if not topic or not topic.get("id"):
                logger.warning("[Essay] 자동 생성: 활성 주제 없음")
                return

            title, content, contributor_cnt, contributor_stats = await generate_essay(
                topic_id=str(topic["id"]),
                topic_title=topic["title"],
                db=db,
                prompt_version="v2",
            )

            essay = Essay(
                topic_id=uuid.UUID(topic["id"]),
                title=title,
                content=content,
                content_type="essay",
                contributor_cnt=contributor_cnt,
                prompt_version="v2",
            )
            db.add(essay)
            await db.commit()
            await db.refresh(essay)

            for user_id, msg_count in contributor_stats.items():
                db.add(EssayContributor(
                    essay_id=essay.id,
                    user_id=uuid.UUID(user_id),
                    message_count=msg_count,
                ))
            await db.commit()
            logger.info("[Essay] 자동 생성 완료: %s (%d명 기여)", title, contributor_cnt)

        except ValueError as e:
            logger.warning("[Essay] 자동 생성 생략: %s", e)
        except Exception as e:
            logger.error("[Essay] 자동 생성 오류: %s", e)
