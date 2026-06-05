from app.services.claude import generate_text
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
import uuid

from app.models.models import SurveyResponse, Conversation

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
[수필 작가·상담 전문가 공동 설계 프롬프트 v1.0]

당신은 따뜻한 문학적 감수성을 가진 수필 작가입니다.
아래 대화 기록은 고독한 이들이 문화적 기억을 통해 나눈 진솔한 이야기입니다.

창작 원칙:
1. 각 목소리는 독립적으로 존중받아야 합니다 — 통합하되 소거하지 마세요
2. 특정 개인을 지칭하는 표현 금지 (모든 주어를 '우리', '어떤 이', '누군가'로)
3. 감정의 과장 금지 — 담담하게 기술하되 울림이 있도록
4. 세대 간 거리를 좁히는 공통 감각을 찾아 연결
5. 마지막 두 문장은 반드시 희망이나 연결감으로 마무리

심리적 안전 원칙:
- 트라우마를 자극할 수 있는 직접적 표현 회피
- 상실·외로움은 인정하되 절망으로 끝내지 않음
- 읽는 이가 자신의 이야기를 발견할 수 있도록 여백 유지

분량: 800~1200자
맨 첫 줄: "[제목: ...]" 형식으로 제목(20자 이내) 작성

대화 기록:
{conversations}
"""


def _select_prompt(version: str) -> str:
    return ESSAY_PROMPT_V1 if version == "v1" else ESSAY_PROMPT_V0


async def _fetch_survey_messages(db: AsyncSession, topic_id: str) -> list[tuple[str, str]]:
    """survey_responses.narrative_text 우선 조회 — (user_id, text) 반환"""
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


async def generate_essay(
    topic_id: str,
    topic_title: str,
    db: AsyncSession,
    prompt_version: str = "v0",
) -> tuple[str, str, int, dict[str, int]]:
    """
    (title, content, contributor_cnt, contributor_stats) 반환
    contributor_stats: {user_id: message_count}
    데이터 소스 우선순위:
    1. survey_responses.narrative_text (신규 구조화 데이터)
    2. conversations(role='user') (구버전 데이터 하위호환)
    """
    # 1. survey_responses 우선
    rows = await _fetch_survey_messages(db, topic_id)

    # 2. 부족하면 conversations 폴백
    if len(rows) < 5:
        rows = await _fetch_conversation_messages(db, topic_id)

    if len(rows) < 5:
        raise ValueError("수필 생성을 위해 최소 5건의 대화가 필요합니다.")

    # 기여자별 메시지 수 집계
    contributor_stats: dict[str, int] = {}
    for user_id, _ in rows:
        contributor_stats[user_id] = contributor_stats.get(user_id, 0) + 1
    contributor_cnt = len(contributor_stats)

    messages = [text for _, text in rows]
    summaries = [f"- {m[:200]}" for m in messages[:20]]
    prompt = _select_prompt(prompt_version).format(
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
    return title, content, contributor_cnt, contributor_stats
