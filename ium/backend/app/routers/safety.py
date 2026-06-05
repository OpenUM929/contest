from fastapi import APIRouter, Depends
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from pydantic import BaseModel
import uuid

from app.database import get_db
from app.models.models import SafetyAlert, User
from app.services.alert import check_no_contact, get_recent_emotions, trigger_alert
from app.services.emotion import check_emotion_trend

router = APIRouter(prefix="/safety", tags=["safety"])


@router.get("/check/{user_id}", summary="사용자 안전 상태 점검")
async def check_user_safety(user_id: str, db: AsyncSession = Depends(get_db)):
    alerts_triggered = []

    # 1. 접속 단절 확인
    no_contact = await check_no_contact(db, user_id)
    if no_contact:
        a = await trigger_alert(db, user_id, "no_contact", "yellow", "3일 이상 미접속")
        alerts_triggered.append({"type": "no_contact", "severity": "yellow"})

    # 2. 감정 악화 추세 확인
    recent = await get_recent_emotions(db, user_id, days=7)
    trend_level = await check_emotion_trend(recent)
    if trend_level:
        a = await trigger_alert(db, user_id, "emotion_drop", trend_level, f"최근 감정 하락 추세")
        alerts_triggered.append({"type": "emotion_drop", "severity": trend_level})

    return {
        "user_id": user_id,
        "no_contact": no_contact,
        "emotion_trend_alert": trend_level,
        "alerts_triggered": alerts_triggered,
        "recent_emotions": recent,
    }


@router.get("/alerts", summary="미해결 알림 목록 (복지사용)")
async def list_alerts(resolved: bool = False, db: AsyncSession = Depends(get_db)):
    result = await db.execute(
        select(SafetyAlert)
        .where(SafetyAlert.resolved == resolved)
        .order_by(SafetyAlert.created_at.desc())
        .limit(50)
    )
    alerts = result.scalars().all()
    return [
        {
            "alert_id": str(a.id),
            "user_id": str(a.user_id),
            "type": a.alert_type,
            "severity": a.severity,
            "note": a.note,
            "created_at": a.created_at.isoformat(),
        }
        for a in alerts
    ]


@router.patch("/alerts/{alert_id}/resolve", summary="알림 해결 처리")
async def resolve_alert(alert_id: str, db: AsyncSession = Depends(get_db)):
    result = await db.execute(
        select(SafetyAlert).where(SafetyAlert.id == uuid.UUID(alert_id))
    )
    alert = result.scalar_one_or_none()
    if not alert:
        from fastapi import HTTPException
        raise HTTPException(status_code=404, detail="알림을 찾을 수 없습니다.")
    alert.resolved = True
    await db.commit()
    return {"status": "resolved"}
