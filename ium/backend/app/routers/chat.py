from fastapi import APIRouter, Depends, HTTPException, UploadFile, File, Query
from fastapi.responses import StreamingResponse, Response
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, func
from sqlalchemy.orm import selectinload
from pydantic import BaseModel
from datetime import datetime
import uuid
import json

from app.database import get_db
from app.models.models import User, Conversation, WeeklyTopic, SurveyResponse, WelfareWorker, Essay, TopicDistribution
from app.services import claude, emotion, alert, voice, public_data

router = APIRouter(prefix="/api/chat", tags=["chat"])


class ChatRequest(BaseModel):
    user_id: str
    message: str
    # 설문지 응답 연동 (선택)
    question_id: str | None = None          # "q1", "q2"
    selected_option_id: str | None = None   # "opt_1", "opt_other"
    selected_option_label: str | None = None # "채소·생선 좌판"
    # 과거 주제 재참여 (선택, 없으면 현재 활성 주제 사용)
    topic_id: str | None = None


class UserCreate(BaseModel):
    user_type: str   # elder | youth
    nickname: str | None = None
    welfare_id: str | None = None


@router.post("/users", summary="사용자 등록")
async def create_user(body: UserCreate, db: AsyncSession = Depends(get_db)):
    user = User(
        user_type=body.user_type,
        nickname=body.nickname or f"익명_{uuid.uuid4().hex[:6]}",
        is_anonymous=(body.user_type == "youth"),
        welfare_id=uuid.UUID(body.welfare_id) if body.welfare_id else None,
    )
    db.add(user)
    await db.commit()
    await db.refresh(user)
    return {"user_id": str(user.id), "user_type": user.user_type, "nickname": user.nickname}


@router.post("/message", summary="텍스트 대화 (스트리밍)")
async def chat_message(body: ChatRequest, db: AsyncSession = Depends(get_db)):
    # 사용자 조회
    result = await db.execute(select(User).where(User.id == uuid.UUID(body.user_id)))
    user = result.scalar_one_or_none()
    if not user:
        raise HTTPException(status_code=404, detail="사용자를 찾을 수 없습니다.")

    # last_seen 갱신
    user.last_seen_at = datetime.utcnow()
    await db.commit()

    # topic_id가 제공되면 해당 주제 직접 조회, 없으면 지역 기반 현재 주제
    topic = None
    topic_uuid = None
    if body.topic_id:
        t_result = await db.execute(
            select(WeeklyTopic).where(WeeklyTopic.id == uuid.UUID(body.topic_id))
        )
        wt = t_result.scalar_one_or_none()
        if wt:
            topic = _topic_to_dict(wt)
            topic_uuid = wt.id
    else:
        # 사용자 지역 조회 (welfare_id → region)
        region = "default"
        if user.welfare_id:
            w_result = await db.execute(
                select(WelfareWorker.region).where(WelfareWorker.id == user.welfare_id)
            )
            region = w_result.scalar_one_or_none() or "default"
        # 이번 주 주제 (담당 복지사 우선 → 지역 → 중앙)
        topic = await public_data.get_active_topic(db, region=region, welfare_id=user.welfare_id)
        if topic and topic.get("id"):
            topic_uuid = uuid.UUID(topic["id"])

    # 최근 대화 이력 (컨텍스트용)
    hist_result = await db.execute(
        select(Conversation)
        .where(Conversation.user_id == user.id)
        .order_by(Conversation.created_at.desc())
        .limit(10)
    )
    history_rows = list(reversed(hist_result.scalars().all()))
    history = [{"role": r.role, "content": r.content} for r in history_rows]

    # 사용자 메시지 저장
    user_conv = Conversation(
        user_id=user.id,
        role="user",
        content=body.message,
        topic_id=topic_uuid,
    )
    db.add(user_conv)

    # 설문지 응답 동시 저장 (question_id 제공 시)
    if body.question_id and not topic_uuid:
        # 유효한 주제가 없으면 설문 응답을 저장할 수 없음 → 잘못된 요청
        raise HTTPException(
            status_code=400,
            detail="유효한 주제 ID가 없습니다. 담당 복지사가 주제를 발행한 뒤 응답해 주세요.",
        )
    if body.question_id and topic_uuid:
        try:
            q_type = "narrative"
            if topic and isinstance(topic.get("choices"), dict):
                for q in topic["choices"].get("questions", []):
                    if q.get("id") == body.question_id:
                        q_type = q.get("type", "narrative")
                        break
            survey_resp = SurveyResponse(
                topic_id=topic_uuid,
                user_id=user.id,
                question_id=body.question_id,
                question_type=q_type,
                selected_option_id=body.selected_option_id,
                selected_option_label=body.selected_option_label,
                narrative_text=body.message if q_type == "narrative" else None,
            )
            db.add(survey_resp)
        except Exception as e:
            print(f"[Chat] survey_response 저장 실패 (무시): {e}")

    # 위기 감지
    crisis_level = claude.detect_crisis_level(body.message)
    if crisis_level:
        await alert.trigger_alert(
            db, user.id, "crisis", "red" if crisis_level == "high" else "yellow",
            note=f"키워드 감지: {crisis_level}"
        )

    # 감정 분석 (비동기, 저장)
    emo = await emotion.analyze(body.message)
    user_conv.emotion_label = emo["label"]
    user_conv.emotion_score = emo["score"]
    await db.commit()

    # 스트리밍 응답
    async def stream_gen():
        full = ""
        async for chunk in claude.stream_chat(user.user_type, topic, history, body.message, crisis_level=crisis_level):
            full += chunk
            yield chunk

        ai_conv = Conversation(user_id=user.id, role="assistant", content=full, topic_id=topic_uuid)
        db.add(ai_conv)
        await db.commit()

    headers = {"X-Crisis-Level": crisis_level} if crisis_level else {}
    return StreamingResponse(stream_gen(), media_type="text/plain; charset=utf-8", headers=headers)


@router.post("/voice/stt", summary="음성 → 텍스트 (Phase 2)")
async def voice_stt(file: UploadFile = File(...)):
    audio_bytes = await file.read()
    text = await voice.speech_to_text(audio_bytes)
    return {"text": text}


@router.post("/voice/tts", summary="텍스트 → 음성 (Phase 2)")
async def voice_tts(body: ChatRequest):
    audio = await voice.text_to_speech(body.message)
    return Response(content=audio, media_type="audio/mpeg")


@router.get("/topic", summary="이번 주 주제 조회 (지역 기반)")
async def get_topic(user_id: str, db: AsyncSession = Depends(get_db)):
    """사용자의 지역에 맞는 이번 주 주제를 조회합니다."""
    # 사용자의 welfare_id → region 조회
    result = await db.execute(
        select(User.welfare_id).where(User.id == uuid.UUID(user_id))
    )
    welfare_id = result.scalar_one_or_none()
    
    region = "default"
    worker_name = None
    if welfare_id:
        w_result = await db.execute(
            select(WelfareWorker).where(WelfareWorker.id == welfare_id)
        )
        worker = w_result.scalar_one_or_none()
        if worker:
            region = worker.region or "default"
            worker_name = worker.name
    
    topic = await public_data.get_active_topic(db, region=region, welfare_id=welfare_id)
    if isinstance(topic, dict):
        topic["distributed_by"] = worker_name
        topic["distributed_by_id"] = str(welfare_id) if welfare_id else None
    return topic


@router.get("/active-topic", summary="현재 활성 주제 조회 (사용자 화면용)")
async def get_active_topic_for_user(
    user_id: str = Query(..., description="사용자 ID"),
    db: AsyncSession = Depends(get_db),
):
    """사용자의 지역에 맞는 현재 활성 주제를 반환합니다."""
    result = await db.execute(select(User).where(User.id == uuid.UUID(user_id)))
    user = result.scalar_one_or_none()
    if not user:
        raise HTTPException(status_code=404, detail="사용자를 찾을 수 없습니다.")

    region = "default"
    worker_name = None
    if user.welfare_id:
        w_result = await db.execute(
            select(WelfareWorker).where(WelfareWorker.id == user.welfare_id)
        )
        worker = w_result.scalar_one_or_none()
        if worker:
            region = worker.region or "default"
            worker_name = worker.name

    topic = await public_data.get_active_topic(db, region=region, welfare_id=user.welfare_id)
    if not topic:
        raise HTTPException(status_code=404, detail="이번 주 활성 주제가 없습니다.")

    if isinstance(topic, dict):
        topic["distributed_by"] = worker_name
        topic["distributed_by_id"] = str(user.welfare_id) if user.welfare_id else None
    return topic


class AcknowledgeRequest(BaseModel):
    user_id: str


@router.post("/topic/{topic_id}/acknowledge", summary="주제 확인 기록")
async def acknowledge_topic(
    topic_id: str,
    body: AcknowledgeRequest,
    db: AsyncSession = Depends(get_db),
):
    """사용자가 주제를 확인했음을 기록합니다."""
    dist_result = await db.execute(
        select(TopicDistribution).where(
            TopicDistribution.topic_id == uuid.UUID(topic_id),
            TopicDistribution.user_id == uuid.UUID(body.user_id),
        )
    )
    dist = dist_result.scalar_one_or_none()
    if not dist:
        dist = TopicDistribution(
            topic_id=uuid.UUID(topic_id),
            user_id=uuid.UUID(body.user_id),
        )
        db.add(dist)

    dist.acknowledged = True
    dist.acknowledged_at = datetime.utcnow()
    await db.commit()

    return {"status": "ok", "acknowledged_at": dist.acknowledged_at.isoformat()}


@router.get("/users/{user_id}/my-surveys", summary="내 설문 응답 누적 보기")
async def get_my_surveys(user_id: str, db: AsyncSession = Depends(get_db)):
    """해당 사용자가 모든 주제에 대해 작성한 설문 응답 이력을 반환합니다."""
    result = await db.execute(
        select(User).where(User.id == uuid.UUID(user_id))
    )
    user = result.scalar_one_or_none()
    if not user:
        raise HTTPException(status_code=404, detail="사용자를 찾을 수 없습니다.")

    # 사용자의 모든 응답 조회 (topic_id 기준 그룹핑)
    resp_result = await db.execute(
        select(SurveyResponse, WeeklyTopic)
        .join(WeeklyTopic, SurveyResponse.topic_id == WeeklyTopic.id)
        .where(SurveyResponse.user_id == uuid.UUID(user_id))
        .order_by(SurveyResponse.responded_at.desc())
    )
    rows = resp_result.all()

    # topic_id 기준으로 그룹핑
    topics_map: dict[str, dict] = {}
    for resp, topic in rows:
        tid = str(resp.topic_id)
        if tid not in topics_map:
            topics_map[tid] = {
                "topic_id": tid,
                "topic_title": topic.title,
                "active_week": topic.active_week.isoformat() if topic.active_week else None,
                "responses": [],
            }
        topics_map[tid]["responses"].append({
            "question_id": resp.question_id,
            "question_type": resp.question_type,
            "selected_option_id": resp.selected_option_id,
            "selected_option_label": resp.selected_option_label,
            "narrative_text": resp.narrative_text,
            "responded_at": resp.responded_at.isoformat() if resp.responded_at else None,
        })

    return {
        "user_id": user_id,
        "nickname": user.nickname,
        "topics": list(topics_map.values()),
    }


# ── 사용자 전용 화면 API ──


@router.get("/users/{user_id}/profile", summary="사용자 프로필 (사용자 화면용)")
async def get_user_profile(user_id: str, db: AsyncSession = Depends(get_db)):
    result = await db.execute(select(User).where(User.id == uuid.UUID(user_id)))
    user = result.scalar_one_or_none()
    if not user:
        raise HTTPException(status_code=404, detail="사용자를 찾을 수 없습니다.")

    return {
        "user_id": str(user.id),
        "user_type": user.user_type,
        "nickname": user.nickname,
        "created_at": user.created_at.isoformat() if user.created_at else None,
        "last_seen_at": user.last_seen_at.isoformat() if user.last_seen_at else None,
    }


@router.get("/surveys/{topic_id}/my-analytics", summary="내 설문 통계 (사용자 화면용)")
async def get_my_survey_analytics(
    topic_id: str,
    user_id: str = Query(...),
    db: AsyncSession = Depends(get_db),
):
    # 사용자 확인
    u_result = await db.execute(select(User).where(User.id == uuid.UUID(user_id)))
    user = u_result.scalar_one_or_none()
    if not user:
        raise HTTPException(status_code=404, detail="사용자를 찾을 수 없습니다.")

    # 주제 확인
    t_result = await db.execute(select(WeeklyTopic).where(WeeklyTopic.id == uuid.UUID(topic_id)))
    topic = t_result.scalar_one_or_none()
    if not topic:
        raise HTTPException(status_code=404, detail="주제를 찾을 수 없습니다.")

    # 내가 응답했는지 확인
    my_resp = await db.execute(
        select(SurveyResponse).where(
            SurveyResponse.topic_id == uuid.UUID(topic_id),
            SurveyResponse.user_id == user.id,
        )
    )
    my_rows = my_resp.scalars().all()
    if not my_rows:
        raise HTTPException(status_code=403, detail="이 설문에 응답하지 않았습니다.")

    # choices 파싱
    questions = []
    if topic.choices:
        try:
            parsed = json.loads(topic.choices)
            if isinstance(parsed, dict) and parsed.get("schema_version") == "1.0":
                questions = parsed.get("questions", [])
        except Exception:
            questions = []

    # 전체 응답자 수
    total_rd = await db.execute(
        select(func.count(func.distinct(SurveyResponse.user_id)))
        .where(SurveyResponse.topic_id == uuid.UUID(topic_id))
    )
    total_respondents = total_rd.scalar() or 0

    result = {
        "topic_id": topic_id,
        "topic_title": topic.title,
        "total_respondents": total_respondents,
        "my_responses": [],
    }

    my_by_q: dict[str, SurveyResponse] = {}
    for r in my_rows:
        my_by_q[r.question_id] = r

    for q in questions:
        q_id = q.get("id")
        q_type = q.get("type")
        q_text = q.get("text", "")
        my_row = my_by_q.get(q_id)

        entry = {
            "question_id": q_id,
            "question_type": q_type,
            "question_text": q_text,
        }

        if q_type == "choice":
            entry["my_answer"] = my_row.selected_option_label if my_row else None
            stats = []
            for opt in q.get("options", []):
                opt_label = opt.get("label")
                cnt_r = await db.execute(
                    select(func.count(SurveyResponse.id))
                    .where(
                        SurveyResponse.topic_id == uuid.UUID(topic_id),
                        SurveyResponse.question_id == q_id,
                        SurveyResponse.selected_option_id == opt.get("id"),
                    )
                )
                cnt = cnt_r.scalar() or 0
                pct = round(cnt * 100.0 / total_respondents, 1) if total_respondents else 0.0
                stats.append({"label": opt_label, "count": cnt, "percent": pct})
            entry["statistics"] = stats
        elif q_type == "narrative":
            entry["my_answer"] = my_row.narrative_text if my_row else None
            narr_r = await db.execute(
                select(SurveyResponse)
                .where(
                    SurveyResponse.topic_id == uuid.UUID(topic_id),
                    SurveyResponse.question_id == q_id,
                    SurveyResponse.narrative_text != None,
                    SurveyResponse.user_id != user.id,
                )
                .order_by(SurveyResponse.responded_at.desc())
                .limit(10)
            )
            others = narr_r.scalars().all()
            entry["sample_responses"] = [
                {"text": nr.narrative_text, "responded_at": nr.responded_at.isoformat() if nr.responded_at else None}
                for nr in others if nr.narrative_text
            ]
            cnt_r = await db.execute(
                select(func.count(SurveyResponse.id))
                .where(
                    SurveyResponse.topic_id == uuid.UUID(topic_id),
                    SurveyResponse.question_id == q_id,
                    SurveyResponse.narrative_text != None,
                )
            )
            entry["response_count"] = cnt_r.scalar() or 0

        result["my_responses"].append(entry)

    return result


class SingleSurveyResponse(BaseModel):
    question_id: str
    question_type: str  # "choice" | "narrative"
    selected_option_id: str | None = None
    selected_option_label: str | None = None
    narrative_text: str | None = None


class SurveyRespondRequest(BaseModel):
    user_id: str
    responses: list[SingleSurveyResponse]


@router.post("/surveys/{topic_id}/respond", summary="설문 답변 제출 (사용자 화면용)")
async def submit_survey_response(
    topic_id: str,
    body: SurveyRespondRequest,
    db: AsyncSession = Depends(get_db),
):
    u_result = await db.execute(select(User).where(User.id == uuid.UUID(body.user_id)))
    user = u_result.scalar_one_or_none()
    if not user:
        raise HTTPException(status_code=404, detail="사용자를 찾을 수 없습니다.")

    t_result = await db.execute(select(WeeklyTopic).where(WeeklyTopic.id == uuid.UUID(topic_id)))
    topic = t_result.scalar_one_or_none()
    if not topic:
        raise HTTPException(status_code=404, detail="주제를 찾을 수 없습니다.")

    now = datetime.utcnow()
    for resp in body.responses:
        sr = SurveyResponse(
            topic_id=topic.id,
            user_id=user.id,
            question_id=resp.question_id,
            question_type=resp.question_type,
            selected_option_id=resp.selected_option_id,
            selected_option_label=resp.selected_option_label,
            narrative_text=resp.narrative_text if resp.question_type == "narrative" else None,
            responded_at=now,
        )
        db.add(sr)
    await db.commit()

    return {"status": "ok", "topic_id": topic_id, "response_count": len(body.responses)}


@router.put("/surveys/{topic_id}/respond", summary="설문 답변 수정 (기존 응답 덮어쓰기)")
async def update_survey_response(
    topic_id: str,
    body: SurveyRespondRequest,
    db: AsyncSession = Depends(get_db),
):
    u_result = await db.execute(select(User).where(User.id == uuid.UUID(body.user_id)))
    user = u_result.scalar_one_or_none()
    if not user:
        raise HTTPException(status_code=404, detail="사용자를 찾을 수 없습니다.")

    t_result = await db.execute(select(WeeklyTopic).where(WeeklyTopic.id == uuid.UUID(topic_id)))
    topic = t_result.scalar_one_or_none()
    if not topic:
        raise HTTPException(status_code=404, detail="주제를 찾을 수 없습니다.")

    # 기존 응답 삭제
    old = await db.execute(
        select(SurveyResponse).where(
            SurveyResponse.topic_id == topic.id,
            SurveyResponse.user_id == user.id,
        )
    )
    for r in old.scalars().all():
        await db.delete(r)

    # 새 응답 저장
    now = datetime.utcnow()
    for resp in body.responses:
        sr = SurveyResponse(
            topic_id=topic.id,
            user_id=user.id,
            question_id=resp.question_id,
            question_type=resp.question_type,
            selected_option_id=resp.selected_option_id,
            selected_option_label=resp.selected_option_label,
            narrative_text=resp.narrative_text if resp.question_type == "narrative" else None,
            responded_at=now,
        )
        db.add(sr)
    await db.commit()

    return {"status": "ok", "topic_id": topic_id, "response_count": len(body.responses)}


@router.get("/content", summary="콘텐츠 라이브러리 (사용자 화면용)")
async def get_content_library(db: AsyncSession = Depends(get_db)):
    # 현재 모듈: 수필(essay)
    e_result = await db.execute(
        select(Essay).order_by(Essay.published_at.desc()).limit(50)
    )
    essays = e_result.scalars().all()

    return {
        "modules": [
            {
                "module_id": "essay",
                "title": "수필",
                "icon": "📖",
                "items": [
                    {
                        "id": str(e.id),
                        "title": e.title or "(제목 없음)",
                        "content": e.content,
                        "content_type": e.content_type,
                        "contributor_cnt": e.contributor_cnt,
                        "published_at": e.published_at.isoformat() if e.published_at else None,
                    }
                    for e in essays
                ],
            }
        ],
    }


def _topic_to_dict(topic: WeeklyTopic) -> dict:
    """WeeklyTopic ORM 객체를 API 응답용 dict로 변환합니다."""
    choices = None
    if topic.choices and topic.choices not in ("null", "None", ""):
        try:
            raw = json.loads(topic.choices)
            if isinstance(raw, dict):
                choices = raw
            elif isinstance(raw, list):
                choices = raw
        except Exception:
            choices = None
    ai_question = topic.ai_question
    if not ai_question and isinstance(choices, dict) and choices.get("questions"):
        ai_question = choices["questions"][0].get("text", "")
    return {
        "id": str(topic.id),
        "title": topic.title,
        "description": topic.description,
        "media_url": topic.media_url,
        "media_type": topic.media_type,
        "source": topic.source,
        "source_url": topic.source_url,
        "ai_question": ai_question,
        "text_content": topic.text_content,
        "question_type": topic.question_type,
        "choices": choices,
        "active_week": topic.active_week.isoformat() if topic.active_week else None,
        "region": topic.region,
    }


@router.get("/users/{user_id}/available-surveys", summary="사용자에게 배포된 모든 WeeklyTopic 목록")
async def get_available_surveys(user_id: str, db: AsyncSession = Depends(get_db)):
    """사용자에게 제공된 모든 WeeklyTopic 목록을 반환합니다 (과거 주제 포함).
    각 항목마다 사용자의 답변 여부(has_responded)를 함께 제공합니다."""
    result = await db.execute(select(User).where(User.id == uuid.UUID(user_id)))
    user = result.scalar_one_or_none()
    if not user:
        raise HTTPException(status_code=404, detail="사용자를 찾을 수 없습니다.")

    # 담당 복지사 기준 주제 목록 조회 (welfare_id 격리)
    #  - 담당 복지사가 있으면: 그 복지사가 발행한 주제 + 중앙 기본 주제(welfare_id IS NULL)
    #  - 담당 복지사가 없으면: 중앙 기본 주제만
    # 같은 지역에 다른 복지사가 발행한 주제는 노출되지 않는다.
    if user.welfare_id:
        topic_filter = (
            (WeeklyTopic.welfare_id == user.welfare_id)
            | (WeeklyTopic.welfare_id.is_(None))
        )
    else:
        topic_filter = WeeklyTopic.welfare_id.is_(None)

    t_result = await db.execute(
        select(WeeklyTopic)
        .where(topic_filter)
        .order_by(WeeklyTopic.active_week.desc(), WeeklyTopic.created_at.desc())
    )
    all_topics = t_result.scalars().all()

    # 사용자의 응답 여부 + 최종 응답시간을 한 번에 조회
    time_result = await db.execute(
        select(
            SurveyResponse.topic_id,
            func.max(SurveyResponse.responded_at).label("last_responded_at"),
        )
        .where(SurveyResponse.user_id == user.id)
        .group_by(SurveyResponse.topic_id)
    )
    responded_map: dict[str, str | None] = {}
    for row in time_result.all():
        tid = str(row[0])
        responded_map[tid] = row[1].isoformat() if row[1] else None

    surveys = []
    for t in all_topics:
        topic_id = str(t.id)
        has_responded = topic_id in responded_map

        # 전체 응답자 수 계산
        cnt_r = await db.execute(
            select(func.count(func.distinct(SurveyResponse.user_id)))
            .where(SurveyResponse.topic_id == t.id)
        )
        total_respondents = cnt_r.scalar() or 0

        surveys.append({
            "topic_id": topic_id,
            "title": t.title,
            "active_week": t.active_week.isoformat() if t.active_week else None,
            "question_type": t.question_type,
            "media_url": t.media_url,
            "has_responded": has_responded,
            "responded_at": responded_map.get(topic_id),
            "total_respondents": total_respondents,
        })

    return {"user_id": user_id, "surveys": surveys}


@router.get("/topics/{topic_id}", summary="특정 주제 상세 조회")
async def get_topic_by_id(topic_id: str, db: AsyncSession = Depends(get_db)):
    """과거 주제의 상세 정보를 조회합니다. (설문 재참여용)"""
    result = await db.execute(
        select(WeeklyTopic).where(WeeklyTopic.id == uuid.UUID(topic_id))
    )
    topic = result.scalar_one_or_none()
    if not topic:
        raise HTTPException(status_code=404, detail="주제를 찾을 수 없습니다.")
    return _topic_to_dict(topic)
