"""5개 심리 지수 계산 (C-4)"""
from __future__ import annotations
from datetime import datetime, timedelta, timezone

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.models import Conversation, PsychIndex
from app.services.language_pattern import analyze_text
from app.services.participation_pattern import get_participation_summary
import uuid

# 관계 키워드
RELATIONSHIP_KEYWORDS = [
    "엄마", "아빠", "어머니", "아버지", "할머니", "할아버지",
    "친구", "이웃", "선생님", "자녀", "아들", "딸", "손자", "손녀",
    "동생", "언니", "오빠", "형", "누나",
]

# 미래 키워드
FUTURE_KEYWORDS = [
    "할 거야", "하고 싶어", "기대돼", "계획", "다음에", "나중에",
    "언젠가", "해볼게", "가고 싶어", "만나고 싶어", "배우고 싶",
]


def _clamp(val: float, lo: float = 0.0, hi: float = 100.0) -> int:
    return int(max(lo, min(hi, val)))


def _keyword_density(text: str, keywords: list[str]) -> float:
    """텍스트 내 키워드 출현 밀도 (0~1)"""
    if not text:
        return 0.0
    hits = sum(1 for kw in keywords if kw in text)
    return min(hits / max(len(keywords) * 0.3, 1), 1.0)


def calc_indices(
    emotions: list[dict],        # [{"label": "negative"|"positive"|"neutral", "score": float}]
    lang_metrics: dict,          # analyze_text() 결과
    participation: dict,         # get_participation_summary() 결과
    combined_text: str = "",     # 최근 대화 합본 텍스트
) -> dict:
    total_e = len(emotions) or 1
    neg_ratio = sum(1 for e in emotions if e.get("label") == "negative") / total_e
    pos_ratio = sum(1 for e in emotions if e.get("label") == "positive") / total_e

    ttr = lang_metrics.get("ttr", 0.5)
    ngram_rep = lang_metrics.get("ngram_repetition", 0.5)
    sent_var = lang_metrics.get("sentence_length_variance", 0.0)
    active_days = participation.get("active_days", 0)
    trend = participation.get("length_trend", 0.0)

    rel_density = _keyword_density(combined_text, RELATIONSHIP_KEYWORDS)
    future_density = _keyword_density(combined_text, FUTURE_KEYWORDS)

    # 외로움: neg 비율 높고, 관계 키워드 적고, 접속 감소할수록 높음
    loneliness = _clamp(
        neg_ratio * 60
        + (1 - rel_density) * 20
        + max(0, -trend * 10)
        + max(0, (14 - active_days) / 14 * 20)
    )

    # 활력: pos 비율, 접속 빈도, 대화 길이 증가 추이
    vitality = _clamp(
        pos_ratio * 50
        + min(active_days / 14, 1.0) * 30
        + min(max(trend * 5, 0), 20)
    )

    # 인지: 어휘 다양성, n-gram 반복 적음, 문장 길이 분산 높음
    sent_var_norm = min(sent_var / 20.0, 1.0)
    cognition = _clamp(
        ttr * 50
        + (1 - ngram_rep) * 30
        + sent_var_norm * 20
    )

    # 관계: 관계 키워드 밀도
    relationship = _clamp(rel_density * 100)

    # 미래: 미래 키워드 밀도
    future = _clamp(future_density * 100)

    return {
        "loneliness": loneliness,
        "vitality": vitality,
        "cognition": cognition,
        "relationship": relationship,
        "future": future,
        "calculated_at": datetime.now(timezone.utc).isoformat(),
    }


async def compute_and_store(
    user_id: str,
    db: AsyncSession,
    days: int = 14,
) -> dict:
    """DB에서 데이터를 읽어 5개 지수를 계산하고 저장 후 반환"""
    uid = uuid.UUID(user_id)
    since = datetime.now(timezone.utc) - timedelta(days=days)

    conv_result = await db.execute(
        select(Conversation)
        .where(
            Conversation.user_id == uid,
            Conversation.role == "user",
            Conversation.created_at >= since,
        )
        .order_by(Conversation.created_at)
    )
    convs = conv_result.scalars().all()

    emotions = [
        {"label": c.emotion_label or "neutral", "score": c.emotion_score or 0.5}
        for c in convs
    ]
    combined_text = " ".join(c.content for c in convs)
    lang_metrics = analyze_text(combined_text) if combined_text else {"ttr": 0.5, "ngram_repetition": 0.5, "sentence_length_variance": 0.0}
    participation = await get_participation_summary(user_id, db, days)

    indices = calc_indices(emotions, lang_metrics, participation, combined_text)

    record = PsychIndex(
        user_id=uid,
        loneliness=indices["loneliness"],
        vitality=indices["vitality"],
        cognition=indices["cognition"],
        relationship_score=indices["relationship"],
        future=indices["future"],
    )
    db.add(record)
    await db.commit()

    return indices
