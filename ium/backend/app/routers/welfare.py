from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, func
from datetime import datetime, timedelta, date
from typing import Literal
import uuid

from app.database import get_db
import json
from app.models.models import (
    User, Conversation, SafetyAlert, WelfareWorker, WeeklyTopic,
    TopicProposal, SurveyTemplate, SurveyResponse, InterventionLog,
)
from app.services.public_data import (
    get_active_topic,
    search_topic_candidates,
    cache_media,
    generate_topic_question,
    refine_topic_question,
    save_weekly_topic,
    publish_weekly_default_topic,
)
from app.services.question_parser import QuestionSet

router = APIRouter(prefix="/welfare", tags=["welfare"])


def _compute_risk_level(no_contact: bool, active_alerts: int, latest_emotion: str | None, weekly_participated: bool) -> str:
    """위험도 복합 판정: no_contact + active_alerts + 감정 추세 + 참여율 종합"""
    if no_contact or active_alerts > 0:
        return "red"
    if latest_emotion == "negative" or not weekly_participated:
        return "yellow"
    return "green"


@router.get("/dashboard", summary="복지사 대시보드 데이터")
async def dashboard(db: AsyncSession = Depends(get_db)):
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
        level = _compute_risk_level(no_contact, active_alerts, latest_emotion, weekly_participated)
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
    quantity: int = 3
    keyword: str = ""


@router.post("/topics/search", summary="공공 API 후보 검색 (관리자가 타입+수량 선택)")
async def search_candidates(
    body: TopicSearchRequest,
    db: AsyncSession = Depends(get_db),
):
    """관리자가 미디어 타입과 수량을 선택하면, 공공 API에서 후보를 검색합니다."""
    candidates = await search_topic_candidates(
        media_type=body.media_type,
        keyword=body.keyword,
        quantity=body.quantity,
    )
    
    if not candidates:
        raise HTTPException(status_code=404, detail="검색 결과가 없습니다. 다시 시도해주세요.")
    
    return {
        "media_type": body.media_type,
        "quantity_requested": body.quantity,
        "candidates_found": len(candidates),
        "candidates": candidates,
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
    
    return {
        "topic_id": str(topic.id),
        "title": topic.title,
        "region": topic.region,
        "question_type": topic.question_type,
        "published_at": topic.created_at.isoformat() if topic.created_at else None,
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
    qset = await generate_topic_question(
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
    return qset.model_dump(mode="json")


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
async def get_current_survey(db: AsyncSession = Depends(get_db)):
    today = date.today()
    monday = today - timedelta(days=today.weekday())
    result = await db.execute(
        select(WeeklyTopic)
        .where(WeeklyTopic.active_week == monday)
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
async def get_survey_history(weeks: int = 4, db: AsyncSession = Depends(get_db)):
    today = date.today()
    monday = today - timedelta(days=today.weekday())
    start_week = monday - timedelta(weeks=weeks - 1)
    result = await db.execute(
        select(WeeklyTopic)
        .where(WeeklyTopic.active_week >= start_week)
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
async def get_survey_analytics(topic_id: str, db: AsyncSession = Depends(get_db)):
    # topic 존재 확인
    t_result = await db.execute(
        select(WeeklyTopic).where(WeeklyTopic.id == uuid.UUID(topic_id))
    )
    topic = t_result.scalar_one_or_none()
    if not topic:
        raise HTTPException(status_code=404, detail="주제를 찾을 수 없습니다.")

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

    return result


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

    return {"topics": archive}
