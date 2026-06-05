from fastapi import APIRouter, Depends, HTTPException, UploadFile, File
from fastapi.responses import StreamingResponse, Response
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from pydantic import BaseModel
from datetime import datetime
import uuid

from app.database import get_db
from app.models.models import User, Conversation, WeeklyTopic, SurveyResponse, WelfareWorker
from app.services import claude, emotion, alert, voice, public_data

router = APIRouter(prefix="/chat", tags=["chat"])


class ChatRequest(BaseModel):
    user_id: str
    message: str
    # 설문지 응답 연동 (선택)
    question_id: str | None = None          # "q1", "q2"
    selected_option_id: str | None = None   # "opt_1", "opt_other"
    selected_option_label: str | None = None # "채소·생선 좌판"


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

    # 사용자 지역 조회 (welfare_id → region)
    from app.models.models import WelfareWorker
    region = "default"
    if user.welfare_id:
        w_result = await db.execute(
            select(WelfareWorker.region).where(WelfareWorker.id == user.welfare_id)
        )
        region = w_result.scalar_one_or_none() or "default"

    # 이번 주 주제 (지역 기반)
    topic = await public_data.get_active_topic(db, region=region)

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
    topic_uuid = uuid.UUID(topic["id"]) if topic.get("id") else None
    user_conv = Conversation(
        user_id=user.id,
        role="user",
        content=body.message,
        topic_id=topic_uuid,
    )
    db.add(user_conv)

    # 설문지 응답 동시 저장 (question_id 제공 시)
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
            db, str(user.id), "crisis", "red" if crisis_level == "high" else "yellow",
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
        async for chunk in claude.stream_chat(user.user_type, topic, history, body.message):
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
    if welfare_id:
        w_result = await db.execute(
            select(WelfareWorker.region).where(WelfareWorker.id == welfare_id)
        )
        region = w_result.scalar_one_or_none() or "default"
    
    topic = await public_data.get_active_topic(db, region=region)
    return topic


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
