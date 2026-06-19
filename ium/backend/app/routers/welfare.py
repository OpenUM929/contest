from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, func, Integer, case
from datetime import datetime, timedelta, date
from typing import Literal
import uuid

from app.database import get_db
import hashlib
import json
from app.models.models import (
    User, Conversation, SafetyAlert, WelfareWorker, WeeklyTopic,
    TopicProposal, SurveyTemplate, SurveyResponse, InterventionLog,
    TopicDistribution,
)
from app.services.public_data import (
    get_active_topic,
    search_topic_candidates,
    cache_media,
    generate_topic_question,
    refine_topic_question,
    save_weekly_topic,
    publish_weekly_default_topic,
    generate_artifact_analysis,
    fetch_local_culture_data,
)
from app.services.question_parser import QuestionSet, validate_question_quality
from app.services.psych_index import compute_and_store
from app.services.mbti import build_option_pole_map, tally_poles, summarize

router = APIRouter(prefix="/api/welfare", tags=["welfare"])


async def _accumulate_user_mbti(db: AsyncSession, user_id: uuid.UUID) -> dict:
    """사용자가 응답한 모든 설문(주제)에 걸쳐 선택형 응답을 MBTI로 누적 집계한다.
    각 주제의 발행 선택지(weekly_topics.choices)에서 보기→극 매핑을 만들어 응답과 조인한다.
    """
    rows = await db.execute(
        select(
            SurveyResponse.topic_id,
            SurveyResponse.question_id,
            SurveyResponse.selected_option_id,
        ).where(
            SurveyResponse.user_id == user_id,
            SurveyResponse.question_type == "choice",
            SurveyResponse.selected_option_id != None,  # noqa: E711
        )
    )
    by_topic: dict[uuid.UUID, list[tuple[str, str]]] = {}
    for tid, q_id, opt_id in rows.all():
        by_topic.setdefault(tid, []).append((q_id, opt_id))

    counts = {p: 0 for p in "EISNTFJP"}
    survey_count = 0
    for tid, resps in by_topic.items():
        topic = await db.get(WeeklyTopic, tid)
        if not topic:
            continue
        pole_map = build_option_pole_map(topic.choices)
        if not pole_map:
            continue
        c = tally_poles(resps, pole_map)
        if any(c.values()):
            survey_count += 1
        for k, v in c.items():
            counts[k] += v

    summary = summarize(counts)
    summary["survey_count"] = survey_count
    return summary


async def compute_risk_level(user_id: uuid.UUID, db: AsyncSession) -> str:
    """가중치 누적 방식 위험도 판정 (B안)."""
    from app.services.alert import get_recent_emotions
    score = 0
    now = datetime.utcnow()

    # 3일 이상 미접속
    cutoff_3d = now - timedelta(days=3)
    has_recent = await db.execute(
        select(func.count(Conversation.id))
        .where(
            Conversation.user_id == user_id,
            Conversation.role == "user",
            Conversation.created_at >= cutoff_3d,
        )
    )
    if has_recent.scalar() == 0:
        score += 3

    # 미해결 SafetyAlert 존재
    alert_cnt = await db.execute(
        select(func.count(SafetyAlert.id))
        .where(
            SafetyAlert.user_id == user_id,
            SafetyAlert.resolved == False,
        )
    )
    if alert_cnt.scalar() > 0:
        score += 3

    # 최근 7일 부정 감정 비율
    recent_7d = await get_recent_emotions(db, user_id, days=7)
    if recent_7d:
        neg_ratio_7d = sum(1 for e in recent_7d if e["label"] == "negative") / len(recent_7d)
        if neg_ratio_7d > 0.6:
            score += 2
        cutoff_3d_ts = now - timedelta(days=3)
        recent_3d = [e for e in recent_7d if e["date"] >= cutoff_3d_ts.date().isoformat()]
        if recent_3d:
            neg_ratio_3d = sum(1 for e in recent_3d if e["label"] == "negative") / len(recent_3d)
            if neg_ratio_3d > 0.8:
                score += 1

    # 최근 7일 접속 횟수
    session_cnt = await db.execute(
        select(func.count(Conversation.id))
        .where(
            Conversation.user_id == user_id,
            Conversation.role == "user",
            Conversation.created_at >= now - timedelta(days=7),
        )
    )
    if session_cnt.scalar() < 2:
        score += 1

    if score >= 6:
        return "red"
    if score >= 3:
        return "yellow"
    return "green"


@router.get("/workers", summary="복지사 목록")
async def list_workers(db: AsyncSession = Depends(get_db)):
    """모든 복지사 목록을 반환합니다."""
    result = await db.execute(
        select(WelfareWorker).where(WelfareWorker.role == "worker").order_by(WelfareWorker.name)
    )
    workers = result.scalars().all()
    return {
        "workers": [
            {
                "welfare_id": str(w.id),
                "name": w.name,
                "region": w.region,
            }
            for w in workers
        ]
    }


@router.get("/dashboard", summary="복지사 대시보드 데이터")
async def dashboard(db: AsyncSession = Depends(get_db)):
    import logging
    logger = logging.getLogger("ium.welfare")
    
    try:
        # 전체 elder 사용자 목록
        result = await db.execute(
            select(User).where(User.user_type == "elder")
        )
        users = result.scalars().all()

        cutoff_3d = datetime.utcnow() - timedelta(days=3)
        week_start = datetime.utcnow() - timedelta(days=datetime.utcnow().weekday())

        summary = []
        red_cnt = yellow_cnt = green_cnt = 0

        for user in users:
            try:
                # 미접속 여부
                no_contact = (user.last_seen_at is None or user.last_seen_at < cutoff_3d)

                # 미해결 알림 수 및 ID 목록
                alert_result = await db.execute(
                    select(SafetyAlert.id, SafetyAlert.severity)
                    .where(SafetyAlert.user_id == user.id, SafetyAlert.resolved == False)
                    .order_by(SafetyAlert.created_at.desc())
                )
                alert_rows = alert_result.all()
                active_alerts = len(alert_rows)
                active_alert_ids = [str(row[0]) for row in alert_rows]

                # 감정 최근 상태
                emotion_result = await db.execute(
                    select(Conversation.emotion_label)
                    .where(
                        Conversation.user_id == user.id,
                        Conversation.role == "user",
                        Conversation.emotion_label != None,
                    )
                    .order_by(Conversation.created_at.desc())
                    .limit(1)
                )
                latest_emotion = emotion_result.scalar_one_or_none()

                # 이번 주 참여 여부
                part_result = await db.execute(
                    select(func.count(Conversation.id))
                    .where(
                        Conversation.user_id == user.id,
                        Conversation.role == "user",
                        Conversation.created_at >= week_start,
                    )
                )
                weekly_participated = (part_result.scalar() or 0) > 0

                # 위험도 복합 판정
                level = await compute_risk_level(user.id, db)
                if level == "red":
                    red_cnt += 1
                elif level == "yellow":
                    yellow_cnt += 1
                else:
                    green_cnt += 1

                summary.append({
                    "user_id": str(user.id),
                    "nickname": user.nickname,
                    "level": level,
                    "last_seen": user.last_seen_at.isoformat() if user.last_seen_at else None,
                    "active_alerts": active_alerts,
                    "active_alert_ids": active_alert_ids,
                    "latest_emotion": latest_emotion,
                    "weekly_participated": weekly_participated,
                })
            except Exception as e:
                logger.error(f"[Dashboard] 사용자 {user.id} 처리 중 오류: {e}")
                # 오류 발생한 사용자는 스킵하고 계속 진행
                continue

        # 위험도 순 정렬 (red → yellow → green)
        order = {"red": 0, "yellow": 1, "green": 2}
        summary.sort(key=lambda x: order[x["level"]])

        # 이번 주 참여율 계산
        part_result = await db.execute(
            select(func.count(func.distinct(Conversation.user_id)))
            .where(Conversation.created_at >= week_start, Conversation.role == "user")
        )
        weekly_participants = part_result.scalar() or 0

        return {
            "summary": {"red": red_cnt, "yellow": yellow_cnt, "green": green_cnt},
            "users": summary,
            "weekly_participants": weekly_participants,
            "total_users": len(users),
        }
    except Exception as e:
        logger.error(f"[Dashboard] 대시보드 조회 중 오류: {e}")
        raise HTTPException(status_code=500, detail=f"대시보드 조회 실패: {str(e)}")


@router.get("/users/{user_id}/detail", summary="사용자 상세 (복지사용)")
async def user_detail(user_id: str, db: AsyncSession = Depends(get_db)):
    result = await db.execute(select(User).where(User.id == uuid.UUID(user_id)))
    user = result.scalar_one_or_none()
    if not user:
        raise HTTPException(status_code=404, detail="사용자를 찾을 수 없습니다.")

    # 최근 대화 5건
    conv_result = await db.execute(
        select(Conversation)
        .where(Conversation.user_id == user.id, Conversation.role == "user")
        .order_by(Conversation.created_at.desc())
        .limit(5)
    )
    conversations = conv_result.scalars().all()

    # 알림 이력
    alert_result = await db.execute(
        select(SafetyAlert)
        .where(SafetyAlert.user_id == user.id)
        .order_by(SafetyAlert.created_at.desc())
        .limit(10)
    )
    alerts = alert_result.scalars().all()

    # 개입 이력
    interv_result = await db.execute(
        select(InterventionLog)
        .where(InterventionLog.user_id == user.id)
        .order_by(InterventionLog.created_at.desc())
        .limit(20)
    )
    interventions = interv_result.scalars().all()

    # 심리 지수 계산 (C-5)
    try:
        psych = await compute_and_store(str(user.id), db)
    except Exception:
        psych = None

    return {
        "user_id": str(user.id),
        "nickname": user.nickname,
        "last_seen": user.last_seen_at.isoformat() if user.last_seen_at else None,
        "recent_conversations": [
            {
                "content": c.content[:100],
                "emotion": c.emotion_label,
                "date": c.created_at.isoformat(),
            }
            for c in conversations
        ],
        "alerts": [
            {
                "type": a.alert_type,
                "severity": a.severity,
                "resolved": a.resolved,
                "date": a.created_at.isoformat(),
            }
            for a in alerts
        ],
        "interventions": [
            {
                "id": str(i.id),
                "action_type": i.action_type,
                "note": i.note,
                "date": i.created_at.isoformat(),
            }
            for i in interventions
        ],
        "psych_indices": psych,
    }


# ─────────────────────────────────────
# 관리자용 주제 발행 API
# ─────────────────────────────────────

@router.get("/topics/default", summary="이번 주 중앙 기본 주제 조회")
async def get_default_topic(db: AsyncSession = Depends(get_db)):
    """중앙 기본 주제(region='default')를 조회합니다."""
    topic = await get_active_topic(db, region="default")
    return topic


class TopicSearchRequest(BaseModel):
    media_type: Literal["image", "audio", "text"]
    media_subtype: str = ""
    quantity: int = 20
    page: int = 1
    keyword: str = ""
    region: str = ""


@router.get("/topics/keywords", summary="TOP 10 키워드 목록 반환")
async def get_keywords():
    """KF_AREA 데이터의 TOP 10 키워드 목록을 반환합니다."""
    from pathlib import Path
    kw_path = Path(r"C:\dev\contest\KF_AREA_TOP10_KEYWORDS.json")
    if not kw_path.exists():
        return {"keywords": []}
    with open(kw_path, "r", encoding="utf-8") as fh:
        keywords = json.load(fh)
    return {"keywords": keywords}


@router.post("/topics/search", summary="공공 API 후보 검색 (관리자가 타입+수량 선택)")
async def search_candidates(
    body: TopicSearchRequest,
    db: AsyncSession = Depends(get_db),
):
    """관리자가 미디어 타입과 수량을 선택하면, 공공 API에서 후보를 검색합니다."""
    keyword = body.keyword.strip() if body.keyword else ""
    region = body.region.strip() if body.region else ""
    page = max(1, body.page)
    page_size = max(1, min(50, body.quantity))
    media_subtype = body.media_subtype.strip() if body.media_subtype else ""
    
    # media_type 변환: "story"는 text의 하위 타입
    api_media_type = body.media_type
    subtype_for_search = media_subtype
    if media_subtype == "story":
        api_media_type = "text"
    
    # 키워드/지역 필터링된 후보 검색
    candidates = await search_topic_candidates(
        media_type=api_media_type,
        keyword=keyword,
        quantity=body.quantity,
    )
    
    # 전체 데이터 (게시판용) - 로컬 CSV에서 직접 조회
    all_candidates = await fetch_local_culture_data(
        media_type=api_media_type,
        keyword="",
        region=region,
        quantity=9999,
        media_subtype=subtype_for_search,
    )
    
    total_count = len(all_candidates) if all_candidates else 0
    total_pages = max(1, (total_count + page_size - 1) // page_size)
    
    # 페이징 처리
    start = (page - 1) * page_size
    end = start + page_size
    paginated = (all_candidates or [])[start:end]
    
    keyword_matched = len(candidates) if candidates else 0
    
    return {
        "media_type": body.media_type,
        "media_subtype": media_subtype,
        "keyword": keyword,
        "region": region,
        "keyword_filtered": bool(keyword),
        "keyword_matched": keyword_matched,
        "candidates_found": keyword_matched,
        "candidates": candidates or [],
        "message": f"키워드 '{keyword}'에 해당하는 결과가 없습니다. 전체 목록을 참조하세요." if keyword and keyword_matched == 0 else "",
        "all_candidates_found": total_count,
        "all_candidates": paginated,
        "page": page,
        "page_size": page_size,
        "total_pages": total_pages,
        "total_count": total_count,
    }


class TopicPublishRequest(BaseModel):
    title: str
    description: str | None = None
    media_url: str | None = None
    media_type: str = "text"
    source: str = ""
    source_url: str = ""
    ai_question: str = ""
    text_content: str | None = None
    question_type: Literal["choice", "narrative", "mixed"] = "narrative"
    welfare_id: str | None = None
    is_customized: bool = True
    choices: dict | None = None  # QuestionSet JSON (발행 전 생성·편집된 설문지)
    target_user_ids: list[str] | None = None  # 선택 배포 대상 (None이면 배포 없음)


@router.post("/topics/publish", summary="관리자가 최종 주제 발행")
async def publish_topic(
    body: TopicPublishRequest,
    db: AsyncSession = Depends(get_db),
):
    """관리자가 후보 중 1개를 선택하고 질문 유형을 지정하여 발행합니다."""
    
    # welfare_id로 관리자 지역 조회
    region = "default"
    if body.welfare_id:
        result = await db.execute(
            select(WelfareWorker.region).where(WelfareWorker.id == uuid.UUID(body.welfare_id))
        )
        region = result.scalar_one_or_none() or "default"
    
    topic_data = {
        "title": body.title,
        "description": body.description or "",
        "media_url": body.media_url,
        "media_type": body.media_type,
        "source": body.source,
        "source_url": body.source_url,
        "ai_question": body.ai_question,
        "text_content": body.text_content,
        "question_type": body.question_type,
        "welfare_id": uuid.UUID(body.welfare_id) if body.welfare_id else None,
        "region": region,
        "is_customized": body.is_customized,
        "choices": body.choices,
    }
    
    topic = await save_weekly_topic(db, topic_data)
    
    # 배포 기록 생성: target_user_ids가 있으면 해당 사용자에게만 배포
    distributed_users = []
    if body.welfare_id and body.target_user_ids is not None and len(body.target_user_ids) > 0:
        w_id = uuid.UUID(body.welfare_id)
        user_ids = [uuid.UUID(uid) for uid in body.target_user_ids]
        user_result = await db.execute(
            select(User).where(User.id.in_(user_ids))
        )
        users = user_result.scalars().all()
        
        found_ids = {u.id for u in users}
        for raw_id in user_ids:
            if raw_id not in found_ids:
                raise HTTPException(
                    status_code=400,
                    detail=f"사용자 ID '{raw_id}'를 찾을 수 없습니다.",
                )
        
        for user in users:
            existing = await db.execute(
                select(TopicDistribution).where(
                    TopicDistribution.topic_id == topic.id,
                    TopicDistribution.user_id == user.id,
                )
            )
            if not existing.scalar_one_or_none():
                dist = TopicDistribution(
                    topic_id=topic.id,
                    user_id=user.id,
                    welfare_id=w_id,
                )
                db.add(dist)
                distributed_users.append({
                    "user_id": str(user.id),
                    "nickname": user.nickname,
                    "user_type": user.user_type,
                })
        
        if distributed_users:
            await db.commit()
    
    return {
        "topic_id": str(topic.id),
        "title": topic.title,
        "region": topic.region,
        "question_type": topic.question_type,
        "published_at": topic.created_at.isoformat() if topic.created_at else None,
        "distributed_users": distributed_users,
    }


@router.get("/workers/{welfare_id}/users", summary="복지사 관할 사용자 목록")
async def get_welfare_users(
    welfare_id: str,
    db: AsyncSession = Depends(get_db),
):
    """특정 복지사에게 배정된 사용자 목록을 반환합니다."""
    user_result = await db.execute(
        select(User).where(User.welfare_id == uuid.UUID(welfare_id))
    )
    users = user_result.scalars().all()
    return {
        "users": [
            {
                "user_id": str(u.id),
                "nickname": u.nickname,
                "user_type": u.user_type,
            }
            for u in users
        ]
    }


@router.get("/topics/distribution-summary", summary="이번 주 배포 확인 현황")
async def get_distribution_summary(
    welfare_id: str,
    db: AsyncSession = Depends(get_db),
):
    """이번 주 배포된 주제의 사용자별 확인 현황을 반환합니다."""
    from datetime import date
    today = date.today()
    monday = today - timedelta(days=today.weekday())

    result = await db.execute(
        select(TopicDistribution).join(WeeklyTopic).where(
            WeeklyTopic.active_week == monday,
            TopicDistribution.welfare_id == uuid.UUID(welfare_id),
        )
    )
    distributions = result.scalars().all()

    total = len(distributions)
    acknowledged = sum(1 for d in distributions if d.acknowledged)

    return {
        "total_distributed": total,
        "acknowledged_count": acknowledged,
        "pending_count": total - acknowledged,
        "users": [
            {
                "user_id": str(d.user_id),
                "topic_id": str(d.topic_id),
                "acknowledged": d.acknowledged,
                "acknowledged_at": d.acknowledged_at.isoformat() if d.acknowledged_at else None,
            }
            for d in distributions
        ]
    }


@router.get("/topics/{topic_id}/distribution", summary="주제별 배포 상세 조회")
async def get_topic_distribution(
    topic_id: str,
    db: AsyncSession = Depends(get_db),
):
    """특정 주제의 배포 대상자별 확인 현황을 반환합니다."""
    result = await db.execute(
        select(TopicDistribution).where(
            TopicDistribution.topic_id == uuid.UUID(topic_id),
        )
    )
    distributions = result.scalars().all()

    users_detail = []
    for d in distributions:
        user_result = await db.execute(select(User).where(User.id == d.user_id))
        user = user_result.scalar_one_or_none()
        users_detail.append({
            "user_id": str(d.user_id),
            "nickname": user.nickname if user else "알 수 없음",
            "user_type": user.user_type if user else "unknown",
            "acknowledged": d.acknowledged,
            "acknowledged_at": d.acknowledged_at.isoformat() if d.acknowledged_at else None,
        })

    return {
        "topic_id": topic_id,
        "total": len(users_detail),
        "acknowledged_count": sum(1 for u in users_detail if u["acknowledged"]),
        "users": users_detail,
    }


@router.post("/topics/preview", summary="사용자 화면 미리보기")
async def preview_user_screens(
    body: TopicPublishRequest,
):
    """관리자가 선택한 주제를 노인/청년 사용자 화면으로 미리보기합니다."""
    
    # 노인용 화면 구성
    elder_screen = {
        "type": "elder",
        "header": "이음(以音)",
        "topic_card": {
            "label": "이번 주 이야기",
            "title": body.title,
            "source": f"[{body.source} 제공]",
            "media_url": body.media_url,
            "media_type": body.media_type,
        },
        "ai_question": body.ai_question,
        "interaction": {
            "type": "voice" if body.media_type in ["audio", "image"] else "text",
            "button_label": "누르고 말씀해 주세요" if body.media_type in ["audio", "image"] else "텍스트로 입력",
        },
        "accessibility": {
            "font_size_control": True,
            "voice_read_aloud": True,
        },
    }
    
    # 청년용 화면 구성
    youth_screen = {
        "type": "youth",
        "header": {
            "title": "이음",
            "anon_badge": "👤 익명",
        },
        "topic_card": {
            "label": "이번 주 주제",
            "title": body.title,
            "source": f"[{body.source} 제공]",
            "media_url": body.media_url,
            "media_type": body.media_type,
            "play_button": body.media_type == "audio",
        },
        "ai_question": body.ai_question,
        "input_area": {
            "placeholder": "자유롭게 써주세요  (익명으로 기록됩니다)",
            "submit_label": "전달하기",
        },
        "bottom_menu": ["📖 이번 주 수필", "✨ 내 기록"],
    }
    
    return {
        "preview_for": ["elder", "youth"],
        "elder_screen": elder_screen,
        "youth_screen": youth_screen,
        "question_type": body.question_type,
        "question_type_label": {
            "narrative": "서술형 (자유롭게 이야기/쓰기)",
            "choice": "선택형 (보기 중 선택)",
            "mixed": "혼합형 (선택 + 서술)",
        }.get(body.question_type, "서술형"),
    }


@router.get("/topics/pending", summary="미발행 여부 확인")
async def check_pending(db: AsyncSession = Depends(get_db)):
    """이번 주에 아직 발행하지 않은 관리자 목록을 반환합니다."""
    from datetime import date
    today = date.today()
    monday = today - timedelta(days=today.weekday())
    
    published = await db.execute(
        select(WeeklyTopic.welfare_id)
        .where(
            WeeklyTopic.active_week == monday,
            WeeklyTopic.is_customized == True,
        )
        .distinct()
    )
    published_ids = {row[0] for row in published.all()}
    
    all_workers_result = await db.execute(select(WelfareWorker))
    all_workers_list = all_workers_result.scalars().all()
    pending = []
    for w in all_workers_list:
        if w.id not in published_ids:
            pending.append({
                "welfare_id": str(w.id),
                "name": w.name,
                "region": w.region,
            })

    return {
        "week_start": monday.isoformat(),
        "total_workers": len(all_workers_list),
        "published_count": len(published_ids),
        "pending_count": len(pending),
        "pending_workers": pending,
    }


# ─────────────────────────────────────
# 설문지 통합 관리 API (SurveyManager)
# ─────────────────────────────────────

class GenerateQuestionsRequest(BaseModel):
    title: str
    description: str | None = None
    media_type: str = "text"
    target_age: Literal["elderly", "youth", "both"] = "elderly"
    question_type: Literal["choice", "narrative", "mixed"] = "narrative"
    custom_hint: str = ""
    question_count: int = 1
    narrative_count: int = 1
    choice_count: int = 1


@router.post("/topics/generate-questions", summary="AI에게 질문 생성 요청")
async def generate_questions(body: GenerateQuestionsRequest):
    """instructor 기반으로 선택형/서술형/혼합형 질문을 생성합니다."""
    qset, ai_generated = await generate_topic_question(
        title=body.title,
        description=body.description or "",
        media_type=body.media_type,
        target_age=body.target_age,
        question_type=body.question_type,
        custom_hint=body.custom_hint,
        question_count=body.question_count,
        narrative_count=body.narrative_count,
        choice_count=body.choice_count,
    )
    warnings = validate_question_quality(qset)
    if not ai_generated:
        # AI 호출이 실패해 하드코딩 폴백 템플릿이 쓰인 경우, 복지사가 알 수 있게 경고를 넣는다.
        # (조용히 1차원적 기본 질문이 나가면 프롬프트가 무시된 것처럼 보인다.)
        warnings.insert(0, "AI 생성에 실패해 기본 예시 질문으로 대체되었습니다. 다시 생성하거나 직접 수정해 주세요.")
    result = qset.model_dump(mode="json")
    result["ai_generated"] = ai_generated
    result["warnings"] = warnings
    return result


class RefineQuestionsRequest(BaseModel):
    topic_title: str
    current_question_set: dict
    instruction: str


@router.post("/topics/refine-questions", summary="AI 협의 — 기존 설문지 수정")
async def refine_questions(body: RefineQuestionsRequest):
    """복지사가 자연어로 수정을 요청하면, AI가 기존 설문지를 개선합니다."""
    try:
        current = QuestionSet.model_validate(body.current_question_set)
    except Exception as e:
        raise HTTPException(status_code=422, detail=f"현재 설문지 Schema 오류: {e}")

    refined = await refine_topic_question(
        topic_title=body.topic_title,
        current_question_set=current,
        instruction=body.instruction,
    )
    return refined.model_dump(mode="json")


class ValidateQuestionsRequest(BaseModel):
    question_set: dict


@router.post("/topics/validate-questions", summary="복지사가 수정한 JSON Schema 검증")
async def validate_questions(body: ValidateQuestionsRequest):
    """복지사 편집기에서 수정한 question_set의 유효성을 검증합니다."""
    try:
        validated = QuestionSet.model_validate(body.question_set)
        return {"valid": True, "errors": []}
    except Exception as e:
        return {"valid": False, "errors": [str(e)]}


class SaveDraftRequest(BaseModel):
    welfare_id: str
    title: str
    description: str | None = None
    media_type: str = "text"
    question_type: Literal["choice", "narrative", "mixed"] = "narrative"
    question_set: dict | None = None


@router.post("/topics/save-draft", summary="설문지 임시 저장")
async def save_draft(body: SaveDraftRequest, db: AsyncSession = Depends(get_db)):
    """복지사가 편집 중인 설문지를 임시 저장합니다."""
    proposal = TopicProposal(
        welfare_id=uuid.UUID(body.welfare_id) if body.welfare_id else None,
        mode="simple",
        welfare_input=body.title,
        question_type=body.question_type,
        question_set_json=body.question_set,
        is_draft=True,
        status="pending",
    )
    db.add(proposal)
    await db.commit()
    await db.refresh(proposal)
    return {"proposal_id": str(proposal.id), "status": "draft_saved"}


# ── 이번 주 / 이력 / 복제 / 중지 ──

@router.get("/surveys/current", summary="이번 주 발행된 설문지 조회")
async def get_current_survey(welfare_id: str | None = None, db: AsyncSession = Depends(get_db)):
    today = date.today()
    monday = today - timedelta(days=today.weekday())
    conds = [WeeklyTopic.active_week == monday]
    # welfare_id 제공 시 해당 복지사 주제만 (복지사 간 격리)
    if welfare_id:
        conds.append(WeeklyTopic.welfare_id == uuid.UUID(welfare_id))
    result = await db.execute(
        select(WeeklyTopic)
        .where(*conds)
        .order_by(WeeklyTopic.is_customized.desc())
    )
    topics = result.scalars().all()
    return [
        {
            "topic_id": str(t.id),
            "title": t.title,
            "question_type": t.question_type,
            "region": t.region,
            "is_customized": t.is_customized,
            "created_at": t.created_at.isoformat() if t.created_at else None,
            "choices": json.loads(t.choices) if t.choices else None,
        }
        for t in topics
    ]


@router.get("/surveys/history", summary="최근 N주간 발행 이력")
async def get_survey_history(weeks: int = 4, welfare_id: str | None = None, db: AsyncSession = Depends(get_db)):
    today = date.today()
    monday = today - timedelta(days=today.weekday())
    start_week = monday - timedelta(weeks=weeks - 1)
    conds = [WeeklyTopic.active_week >= start_week]
    # welfare_id 제공 시 해당 복지사 주제만 (복지사 간 격리)
    if welfare_id:
        conds.append(WeeklyTopic.welfare_id == uuid.UUID(welfare_id))
    result = await db.execute(
        select(WeeklyTopic)
        .where(*conds)
        .order_by(WeeklyTopic.active_week.desc(), WeeklyTopic.created_at.desc())
    )
    topics = result.scalars().all()
    return [
        {
            "topic_id": str(t.id),
            "title": t.title,
            "question_type": t.question_type,
            "region": t.region,
            "active_week": t.active_week.isoformat() if t.active_week else None,
            "is_customized": t.is_customized,
        }
        for t in topics
    ]


@router.post("/surveys/{topic_id}/clone", summary="지난 주 설문지를 이번 주 draft로 복제")
async def clone_survey(topic_id: str, db: AsyncSession = Depends(get_db)):
    result = await db.execute(
        select(WeeklyTopic).where(WeeklyTopic.id == uuid.UUID(topic_id))
    )
    base = result.scalar_one_or_none()
    if not base:
        raise HTTPException(status_code=404, detail="주제를 찾을 수 없습니다.")

    proposal = TopicProposal(
        welfare_id=base.welfare_id,
        mode="simple",
        welfare_input=base.title,
        question_type=base.question_type,
        question_set_json=json.loads(base.choices) if base.choices else None,
        is_draft=True,
        status="pending",
    )
    db.add(proposal)
    await db.commit()
    await db.refresh(proposal)
    return {"proposal_id": str(proposal.id), "cloned_from": topic_id}


@router.patch("/surveys/{topic_id}/stop", summary="발행 중지")
async def stop_survey(topic_id: str, db: AsyncSession = Depends(get_db)):
    result = await db.execute(
        select(WeeklyTopic).where(WeeklyTopic.id == uuid.UUID(topic_id))
    )
    topic = result.scalar_one_or_none()
    if not topic:
        raise HTTPException(status_code=404, detail="주제를 찾을 수 없습니다.")

    topic.is_customized = False
    await db.commit()
    return {"topic_id": topic_id, "status": "stopped"}


# ── 편집용 조회 / 수정 ──

@router.get("/surveys/{topic_id}/edit", summary="편집용 데이터 조회")
async def get_survey_for_edit(topic_id: str, db: AsyncSession = Depends(get_db)):
    result = await db.execute(
        select(WeeklyTopic).where(WeeklyTopic.id == uuid.UUID(topic_id))
    )
    topic = result.scalar_one_or_none()
    if not topic:
        raise HTTPException(status_code=404, detail="주제를 찾을 수 없습니다.")

    choices = None
    if topic.choices:
        try:
            raw = json.loads(topic.choices)
            if isinstance(raw, dict) and raw.get("schema_version") == "1.0":
                # Schema 버전은 맞지만 내용이 잘못됐을 수도 있음 → Pydantic 검증
                QuestionSet.model_validate(raw)
                choices = raw
        except Exception:
            choices = None

    # 기존 주제(choices 미저장 또는 손상) 호환용 — 주제 정보로 기본 QuestionSet 합성
    if not choices:
        q_text = topic.ai_question or f"{topic.title}에 대해 이야기해 주세요."
        is_choice_first = topic.question_type in ("choice", "mixed")
        base_q = {
            "id": "q1",
            "type": "choice" if is_choice_first else "narrative",
            "text": q_text,
            "target_age": "elderly",
        }
        if is_choice_first:
            base_q["options"] = [
                {"id": "opt_1", "label": "예", "value": "yes"},
                {"id": "opt_2", "label": "아니오", "value": "no"},
            ]
            base_q["has_other"] = True
            base_q["options"].append({"id": "opt_other", "label": "기타 (직접 말씀해 주세요)", "value": "OTHER", "is_other": True})

        questions = [base_q]
        if topic.question_type == "mixed":
            questions.append({
                "id": "q2",
                "type": "narrative",
                "text": f"{topic.title}와 관련해 가장 기억에 남는 순간을 자유롭게 이야기해 주세요.",
                "target_age": "elderly",
                "placeholder": "그때의 이야기를 들려주세요...",
            })

        choices = {
            "schema_version": "1.0",
            "question_type": topic.question_type or "narrative",
            "questions": questions,
        }

    return {
        "topic_id": str(topic.id),
        "title": topic.title,
        "description": topic.description,
        "media_type": topic.media_type,
        "question_type": topic.question_type,
        "choices": choices,
    }


class SurveyEditRequest(BaseModel):
    title: str
    description: str | None = None
    choices: dict | None = None  # QuestionSet JSON


@router.put("/surveys/{topic_id}/edit", summary="설문지 수정 후 재발행")
async def edit_survey(
    topic_id: str,
    body: SurveyEditRequest,
    db: AsyncSession = Depends(get_db),
):
    result = await db.execute(
        select(WeeklyTopic).where(WeeklyTopic.id == uuid.UUID(topic_id))
    )
    topic = result.scalar_one_or_none()
    if not topic:
        raise HTTPException(status_code=404, detail="주제를 찾을 수 없습니다.")

    if body.choices:
        try:
            validated = QuestionSet.model_validate(body.choices)
            topic.choices = validated.model_dump_json(ensure_ascii=False)
            topic.question_type = validated.question_type
        except Exception as e:
            raise HTTPException(status_code=422, detail=f"Schema 오류: {e}")

    topic.title = body.title
    topic.description = body.description or topic.description
    await db.commit()
    await db.refresh(topic)
    return {"topic_id": topic_id, "status": "updated"}


# ── 템플릿 ──

@router.get("/survey-templates", summary="저장된 템플릿 목록")
async def list_templates(
    welfare_id: str,
    db: AsyncSession = Depends(get_db),
):
    result = await db.execute(
        select(SurveyTemplate)
        .where(SurveyTemplate.welfare_id == uuid.UUID(welfare_id))
        .order_by(SurveyTemplate.updated_at.desc())
    )
    templates = result.scalars().all()
    return [
        {
            "id": str(t.id),
            "name": t.name,
            "created_at": t.created_at.isoformat() if t.created_at else None,
        }
        for t in templates
    ]


class SaveTemplateRequest(BaseModel):
    welfare_id: str
    name: str
    question_set: dict


@router.post("/survey-templates", summary="현재 설문지를 템플릿으로 저장")
async def save_template(body: SaveTemplateRequest, db: AsyncSession = Depends(get_db)):
    try:
        validated = QuestionSet.model_validate(body.question_set)
    except Exception as e:
        raise HTTPException(status_code=422, detail=f"Schema 오류: {e}")

    tmpl = SurveyTemplate(
        welfare_id=uuid.UUID(body.welfare_id),
        name=body.name,
        question_set_json=validated.model_dump(mode="json"),
    )
    db.add(tmpl)
    await db.commit()
    await db.refresh(tmpl)
    return {"template_id": str(tmpl.id), "name": tmpl.name}


# ── 집계 / 응답 조회 ──

@router.get("/surveys/{topic_id}/analytics", summary="보기별 응답 집계 + 서술형 답변 목록")
async def get_survey_analytics(topic_id: str, welfare_id: str | None = None, db: AsyncSession = Depends(get_db)):
    # topic 존재 확인
    t_result = await db.execute(
        select(WeeklyTopic).where(WeeklyTopic.id == uuid.UUID(topic_id))
    )
    topic = t_result.scalar_one_or_none()
    if not topic:
        raise HTTPException(status_code=404, detail="주제를 찾을 수 없습니다.")

    # 소유권 검증: welfare_id 제공 시, 본인 주제(또는 중앙 기본 주제)만 열람 가능
    if welfare_id and topic.welfare_id is not None and topic.welfare_id != uuid.UUID(welfare_id):
        raise HTTPException(status_code=403, detail="다른 복지사의 설문 통계는 열람할 수 없습니다.")

    # choices 파싱
    questions = []
    if topic.choices:
        try:
            parsed = json.loads(topic.choices)
            if isinstance(parsed, dict) and parsed.get("schema_version") == "1.0":
                questions = parsed.get("questions", [])
            elif isinstance(parsed, list):
                questions = []
        except Exception:
            questions = []

    # 전체 응답자 수 (중복 제거)
    total_resp = await db.execute(
        select(func.count(func.distinct(SurveyResponse.user_id)))
        .where(SurveyResponse.topic_id == uuid.UUID(topic_id))
    )
    total_respondents = total_resp.scalar() or 0

    result = {
        "topic_id": topic_id,
        "total_respondents": total_respondents,
        "questions": [],
    }

    for q in questions:
        q_id = q.get("id")
        q_type = q.get("type")
        q_text = q.get("text", "")

        if q_type == "choice":
            # 보기별 집계
            stats = []
            for opt in q.get("options", []):
                opt_id = opt.get("id")
                opt_label = opt.get("label")
                cnt_result = await db.execute(
                    select(func.count(SurveyResponse.id))
                    .where(
                        SurveyResponse.topic_id == uuid.UUID(topic_id),
                        SurveyResponse.question_id == q_id,
                        SurveyResponse.selected_option_id == opt_id,
                    )
                )
                cnt = cnt_result.scalar() or 0
                pct = round(cnt * 100.0 / total_respondents, 1) if total_respondents else 0.0
                stats.append({"label": opt_label, "count": cnt, "percent": pct})
            result["questions"].append({
                "question_id": q_id,
                "type": "choice",
                "text": q_text,
                "options_stats": stats,
            })
        elif q_type == "narrative":
            narr_result = await db.execute(
                select(SurveyResponse.narrative_text)
                .where(
                    SurveyResponse.topic_id == uuid.UUID(topic_id),
                    SurveyResponse.question_id == q_id,
                    SurveyResponse.narrative_text != None,
                )
                .order_by(SurveyResponse.responded_at.desc())
                .limit(10)
            )
            sample_responses = [row[0] for row in narr_result.all() if row[0]]
            count_result = await db.execute(
                select(func.count(SurveyResponse.id))
                .where(
                    SurveyResponse.topic_id == uuid.UUID(topic_id),
                    SurveyResponse.question_id == q_id,
                    SurveyResponse.narrative_text != None,
                )
            )
            response_count = count_result.scalar() or 0
            result["questions"].append({
                "question_id": q_id,
                "type": "narrative",
                "text": q_text,
                "response_count": response_count,
                "sample_responses": sample_responses,
            })

    # MBTI 집계 — 선택형 보기에 mbti_pole 태그가 있을 때만
    pole_map = build_option_pole_map(topic.choices)
    if pole_map:
        # (1) 이 주제 전체 응답 기준 분포
        choice_rows = await db.execute(
            select(SurveyResponse.question_id, SurveyResponse.selected_option_id)
            .where(
                SurveyResponse.topic_id == uuid.UUID(topic_id),
                SurveyResponse.question_type == "choice",
                SurveyResponse.selected_option_id != None,  # noqa: E711
            )
        )
        result["mbti_distribution"] = summarize(tally_poles(choice_rows.all(), pole_map))

        # (2) 응답자별 누적 성향 — 이 주제 응답자 각각을 모든 설문에 걸쳐 누적 집계
        resp_users = await db.execute(
            select(func.distinct(SurveyResponse.user_id))
            .where(SurveyResponse.topic_id == uuid.UUID(topic_id))
        )
        respondent_mbti = []
        for (uid,) in resp_users.all():
            user = await db.get(User, uid)
            acc = await _accumulate_user_mbti(db, uid)
            respondent_mbti.append({
                "user_id": str(uid),
                "nickname": (user.nickname if user else None) or "익명",
                "type": acc["type"],
                "is_complete": acc["is_complete"],
                "survey_count": acc["survey_count"],
                "total_signals": acc["total_signals"],
            })
        result["respondent_mbti"] = respondent_mbti

    return result


@router.get("/users/{user_id}/mbti", summary="사용자 누적 MBTI 성향 (모든 설문 누적)")
async def get_user_mbti(user_id: str, db: AsyncSession = Depends(get_db)):
    """사용자가 응답한 모든 설문의 선택형 응답을 누적해 MBTI 성향을 반환한다.
    설문이 쌓일수록 더 많은 축이 채워지고 추정이 정교해진다.
    """
    u = await db.get(User, uuid.UUID(user_id))
    if not u:
        raise HTTPException(status_code=404, detail="사용자를 찾을 수 없습니다.")
    summary = await _accumulate_user_mbti(db, uuid.UUID(user_id))
    summary["user_id"] = user_id
    summary["nickname"] = u.nickname or "익명"
    return summary


@router.get("/surveys/{topic_id}/responses", summary="전체 응답 원본 조회")
async def get_survey_responses(
    topic_id: str,
    page: int = 1,
    page_size: int = 50,
    db: AsyncSession = Depends(get_db),
):
    offset = (page - 1) * page_size
    result = await db.execute(
        select(SurveyResponse)
        .where(SurveyResponse.topic_id == uuid.UUID(topic_id))
        .order_by(SurveyResponse.responded_at.desc())
        .offset(offset)
        .limit(page_size)
    )
    rows = result.scalars().all()
    return {
        "topic_id": topic_id,
        "page": page,
        "page_size": page_size,
        "responses": [
            {
                "user_id": str(r.user_id),
                "question_id": r.question_id,
                "question_type": r.question_type,
                "selected_option_id": r.selected_option_id,
                "selected_option_label": r.selected_option_label,
                "narrative_text": r.narrative_text,
                "responded_at": r.responded_at.isoformat() if r.responded_at else None,
            }
            for r in rows
        ],
    }


# ─────────────────────────────────────
# 개입 이력 API (InterventionLog)
# ─────────────────────────────────────

class InterventionRequest(BaseModel):
    welfare_id: str | None = None
    action_type: str  # phone | visit | counseling | detail | alert_resolve
    note: str | None = None


@router.post("/users/{user_id}/intervention", summary="개입 이력 기록")
async def record_intervention(
    user_id: str,
    body: InterventionRequest,
    db: AsyncSession = Depends(get_db),
):
    result = await db.execute(select(User).where(User.id == uuid.UUID(user_id)))
    user = result.scalar_one_or_none()
    if not user:
        raise HTTPException(status_code=404, detail="사용자를 찾을 수 없습니다.")

    log = InterventionLog(
        user_id=uuid.UUID(user_id),
        welfare_id=uuid.UUID(body.welfare_id) if body.welfare_id else None,
        action_type=body.action_type,
        note=body.note,
    )
    db.add(log)
    await db.commit()
    await db.refresh(log)
    return {"intervention_id": str(log.id), "status": "recorded"}


@router.get("/users/{user_id}/interventions", summary="사용자 개입 이력 조회")
async def get_interventions(
    user_id: str,
    limit: int = 20,
    db: AsyncSession = Depends(get_db),
):
    result = await db.execute(
        select(InterventionLog)
        .where(InterventionLog.user_id == uuid.UUID(user_id))
        .order_by(InterventionLog.created_at.desc())
        .limit(limit)
    )
    logs = result.scalars().all()
    return [
        {
            "id": str(l.id),
            "action_type": l.action_type,
            "note": l.note,
            "created_at": l.created_at.isoformat(),
        }
        for l in logs
    ]


# ─────────────────────────────────────
# 주제 아카이브 + 통계 요약 (사용자용)
# ─────────────────────────────────────

@router.get("/topics/archive", summary="주제 아카이브 + 통계 요약")
async def get_topics_archive(db: AsyncSession = Depends(get_db)):
    """모든 발행된 주제 목록과 각 주제의 간단한 통계를 반환합니다."""
    result = await db.execute(
        select(WeeklyTopic)
        .order_by(WeeklyTopic.active_week.desc(), WeeklyTopic.created_at.desc())
    )
    topics = result.scalars().all()

    archive = []
    for topic in topics:
        # 응답자 수
        resp_count = await db.execute(
            select(func.count(func.distinct(SurveyResponse.user_id)))
            .where(SurveyResponse.topic_id == topic.id)
        )
        respondents = resp_count.scalar() or 0

        # 수필 존재 여부
        essay_result = await db.execute(
            select(Essay).where(Essay.topic_id == topic.id)
        )
        essay = essay_result.scalar_one_or_none()

        archive.append({
            "topic_id": str(topic.id),
            "title": topic.title,
            "active_week": topic.active_week.isoformat() if topic.active_week else None,
            "question_type": topic.question_type,
            "region": topic.region,
            "respondents": respondents,
            "has_essay": essay is not None,
            "essay_id": str(essay.id) if essay else None,
        })


# ─────────────────────────────────────
# 비식별화 보고 API (G-3)
# ─────────────────────────────────────

@router.get("/report/anonymized", summary="비식별화 대화 통계 보고")
async def anonymized_report(
    days: int = 7,
    db: AsyncSession = Depends(get_db),
):
    """user_id 대신 SHA-256 8자리 코드로 대화 통계 반환"""
    since = datetime.now() - timedelta(days=days)
    period_start = (datetime.now() - timedelta(days=days)).strftime("%Y-%m-%d")
    period_end = datetime.now().strftime("%Y-%m-%d")

    result = await db.execute(
        select(
            Conversation.user_id,
            func.count(Conversation.id).label("msg_count"),
            func.sum(
                case((Conversation.emotion_label == "positive", 1), else_=0)
            ).label("pos_count"),
            func.sum(
                case((Conversation.emotion_label == "negative", 1), else_=0)
            ).label("neg_count"),
        )
        .where(Conversation.created_at >= since, Conversation.role == "user")
        .group_by(Conversation.user_id)
    )
    rows = result.all()

    users = []
    for row in rows:
        code = hashlib.sha256(str(row.user_id).encode()).hexdigest()[:8]
        msg_count = row.msg_count or 0
        pos = row.pos_count or 0
        neg = row.neg_count or 0
        if pos > neg:
            avg_emotion = "positive"
        elif neg > pos:
            avg_emotion = "negative"
        else:
            avg_emotion = "neutral"
        users.append({
            "code": code,
            "message_count": msg_count,
            "avg_emotion": avg_emotion,
        })

    return {
        "period": f"{period_start}~{period_end}",
        "user_count": len(users),
        "users": users,
    }


# ─────────────────────────────────────
# 유물 분석 lazy loading (0609)
# ─────────────────────────────────────

class ArtifactAnalyzeRequest(BaseModel):
    title: str
    description: str = ""
    ingredient: str = ""
    sizing: str = ""
    source: str = ""


@router.post("/topics/analyze", summary="유물 메타데이터 분석 (lazy loading)")
async def analyze_artifact(
    body: ArtifactAnalyzeRequest,
    db: AsyncSession = Depends(get_db),
):
    """복지사가 이미지/유물 카드를 클릭했을 때 상세 분석 결과를 반환합니다.
    검색 시점(eager)에서 분석하지 않고, 카드 클릭 시(lazy)에 분석하여 응답 지연을 줄입니다.
    """
    result = await generate_artifact_analysis(
        title=body.title,
        description=body.description,
        ingredient=body.ingredient,
        sizing=body.sizing,
        source=body.source,
    )
    if result is None:
        raise HTTPException(status_code=500, detail="유물 분석에 실패했습니다.")
    return result.model_dump(mode="json")
