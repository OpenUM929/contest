"""
안전 감지 및 복지사 알림 서비스.
"""
import asyncio
import logging
from datetime import datetime, timedelta, date

from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, func

from app.models.models import SafetyAlert, User, Conversation, WelfareWorker

logger = logging.getLogger("ium.alert")


async def trigger_alert(
    db: AsyncSession,
    user_id: str,
    alert_type: str,
    severity: str,
    note: str = "",
) -> SafetyAlert:
    alert = SafetyAlert(
        user_id=user_id,
        alert_type=alert_type,
        severity=severity,
        note=note,
    )
    db.add(alert)
    await db.commit()
    await db.refresh(alert)

    logger.warning(
        "[ALERT] user=%s type=%s severity=%s note=%s",
        user_id, alert_type, severity, note,
    )

    asyncio.create_task(_send_welfare_email(db, user_id, alert_type, severity, note))
    return alert


async def _send_welfare_email(
    db: AsyncSession,
    user_id: str,
    alert_type: str,
    severity: str,
    note: str,
) -> None:
    from app.services.email_service import send_alert_email
    from app.config import settings

    try:
        user_result = await db.execute(
            select(User).where(User.id == user_id)
        )
        user = user_result.scalar_one_or_none()
        if not user:
            return

        to_email = settings.welfare_notify_email
        if user.welfare_id:
            w_result = await db.execute(
                select(WelfareWorker.email).where(WelfareWorker.id == user.welfare_id)
            )
            worker_email = w_result.scalar_one_or_none()
            if worker_email:
                to_email = worker_email

        if not to_email:
            return

        nickname = user.nickname or "익명"
        short_id = str(user.id)[:8]
        timestamp = datetime.utcnow().strftime("%Y-%m-%d %H:%M UTC")

        if alert_type == "crisis":
            await send_alert_email(
                to_email, "crisis",
                nickname=nickname, short_id=short_id,
                severity=severity, timestamp=timestamp, note=note,
            )
        elif alert_type == "no_contact":
            last_seen = user.last_seen_at.strftime("%Y-%m-%d") if user.last_seen_at else "기록 없음"
            await send_alert_email(
                to_email, "no_contact",
                nickname=nickname, short_id=short_id, last_seen=last_seen,
            )
        elif alert_type == "emotion_drop":
            await send_alert_email(
                to_email, "emotion_drop",
                nickname=nickname, short_id=short_id, trend=note,
            )
    except Exception as exc:
        logger.warning("[Alert] 이메일 발송 실패 (무시): %s", exc)


async def check_no_contact(db: AsyncSession, user_id: str) -> bool:
    result = await db.execute(
        select(User.last_seen_at).where(User.id == user_id)
    )
    last_seen = result.scalar_one_or_none()
    if last_seen is None:
        return True
    return datetime.utcnow() - last_seen > timedelta(days=3)


async def get_recent_emotions(
    db: AsyncSession, user_id: str, days: int = 7
) -> list[dict]:
    cutoff = datetime.utcnow() - timedelta(days=days)
    result = await db.execute(
        select(Conversation.emotion_label, Conversation.created_at)
        .where(
            Conversation.user_id == user_id,
            Conversation.role == "user",
            Conversation.emotion_label != None,
            Conversation.created_at >= cutoff,
        )
        .order_by(Conversation.created_at)
    )
    rows = result.all()
    return [{"label": r.emotion_label, "date": r.created_at.date().isoformat()} for r in rows]


async def daily_safety_check() -> None:
    """매일 09:00 — 전체 elder 사용자 접속 단절 + 감정 악화 일괄 점검."""
    from app.database import AsyncSessionLocal

    logger.info("[SafetyCheck] 일일 안전 점검 시작")

    async with AsyncSessionLocal() as db:
        result = await db.execute(
            select(User).where(User.user_type == "elder")
        )
        users = result.scalars().all()

        today = date.today()

        for user in users:
            uid = str(user.id)

            # 중복 알림 방지: 오늘 이미 같은 타입 알림이 있으면 생략
            existing = await db.execute(
                select(func.count(SafetyAlert.id)).where(
                    SafetyAlert.user_id == user.id,
                    SafetyAlert.resolved == False,
                )
            )
            active_count = existing.scalar() or 0
            if active_count >= 3:
                continue

            # 미접속 체크
            if await check_no_contact(db, uid):
                await trigger_alert(db, uid, "no_contact", "yellow", note="3일 이상 미접속")
                continue

            # 감정 악화 체크: 최근 3건 모두 negative
            emotions = await get_recent_emotions(db, uid, days=3)
            if len(emotions) >= 3:
                recent_labels = [e["label"] for e in emotions[-3:]]
                if all(label == "negative" for label in recent_labels):
                    await trigger_alert(
                        db, uid, "emotion_drop", "yellow",
                        note="최근 3건 연속 부정 감정",
                    )

    logger.info("[SafetyCheck] 일일 안전 점검 완료 (대상: %d명)", len(users))
