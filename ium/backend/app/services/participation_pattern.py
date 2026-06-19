"""참여 패턴 분석 — 일별 접속 횟수, 대화 길이 추이 (C-3)"""
from __future__ import annotations
from datetime import datetime, timedelta, timezone

from sqlalchemy import select, func
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.models import Conversation
import uuid


async def get_daily_session_count(
    user_id: str, db: AsyncSession, days: int = 30
) -> list[dict]:
    """일별 대화 시작 횟수 반환 [{date, count}]"""
    since = datetime.now(timezone.utc) - timedelta(days=days)
    uid = uuid.UUID(user_id)

    result = await db.execute(
        select(
            func.date(Conversation.created_at).label("day"),
            func.count(Conversation.id).label("cnt"),
        )
        .where(
            Conversation.user_id == uid,
            Conversation.role == "user",
            Conversation.created_at >= since,
        )
        .group_by(func.date(Conversation.created_at))
        .order_by(func.date(Conversation.created_at))
    )
    return [{"date": str(row.day), "count": row.cnt} for row in result.all()]


async def calc_conversation_length_trend(
    user_id: str, db: AsyncSession, days: int = 30
) -> float:
    """대화 길이 추이 — 선형 회귀 기울기 (양수=증가, 음수=감소, 0=데이터 부족)"""
    since = datetime.now(timezone.utc) - timedelta(days=days)
    uid = uuid.UUID(user_id)

    result = await db.execute(
        select(
            func.date(Conversation.created_at).label("day"),
            func.avg(func.length(Conversation.content)).label("avg_len"),
        )
        .where(
            Conversation.user_id == uid,
            Conversation.role == "user",
            Conversation.created_at >= since,
        )
        .group_by(func.date(Conversation.created_at))
        .order_by(func.date(Conversation.created_at))
    )
    rows = result.all()
    if len(rows) < 2:
        return 0.0

    xs = list(range(len(rows)))
    ys = [float(r.avg_len or 0) for r in rows]
    x_mean = sum(xs) / len(xs)
    y_mean = sum(ys) / len(ys)
    numerator = sum((x - x_mean) * (y - y_mean) for x, y in zip(xs, ys))
    denominator = sum((x - x_mean) ** 2 for x in xs)
    if denominator == 0:
        return 0.0
    return round(numerator / denominator, 4)


async def get_participation_summary(
    user_id: str, db: AsyncSession, days: int = 30
) -> dict:
    daily = await get_daily_session_count(user_id, db, days)
    trend = await calc_conversation_length_trend(user_id, db, days)
    active_days = len([d for d in daily if d["count"] > 0])
    return {
        "active_days": active_days,
        "daily_counts": daily,
        "length_trend": trend,
    }
