# Pipeline C — 감정 분석 · 심리 지표 상세 구현 계획

> **의존**: Pipeline B (대화 저장 안정화)  
> **영향**: Pipeline E (안전 감지), Pipeline F (복지사 대시보드)  
> **작성 기준일**: 2026년 6월 1일

---

## 현재 코드 상태 (진단)

| 파일 | 위치 | 현재 상태 | 문제 |
|---|---|---|---|
| `backend/app/services/emotion.py` | 24번 줄 | `snunlp/KR-FinBert-SC` 사용 | 금융 도메인 모델 — 일상 대화 정확도 의문 |
| `emotion.py` | 전체 | 긍정/부정/중립 3분류만 | 언어 패턴, 참여 패턴 없음 |
| `emotion.py` | 67~78번 줄 | `check_emotion_trend()` — 최근 7일 중 negative 5회 이상 | 기계적 임계값, 개인차 미반영 |
| `backend/app/routers/welfare.py` | 39~49번 줄 | 최신 감정 1건만 조회 | 추세(trend) 미반영 |
| 전체 코드베이스 | — | TTR, n-gram, 접속 빈도 분석 없음 | 심리 지표 1/5만 구현 |

---

## 구현 목표

```
[현재 구현] 감정 분류 (긍정/부정/중립) — 1개

[추가 구현]
├─ 언어 패턴: TTR(어휘 다양성), 문장 길이, 반복 표현 비율
├─ 참여 패턴: 일별 접속 빈도, 대화 길이 변화
└─ 5개 심리 지수: 외로움 / 활력 / 인지 / 관계 / 미래
```

---

## Step 1 — 감정 모델 실성능 검증

### 1-1. KR-FinBert-SC 문제 분석

- 원래 용도: 금융 뉴스 감성 분류 (긍/부/중)
- 학습 데이터: 금융 도메인 텍스트
- 이음 사용 목적: 노인의 일상 대화 ("오늘 외로웠어요", "옛날 생각이 나요")
- 도메인 미스매치 → 정확도 저하 가능성

### 1-2. 대안 모델 검토

| 모델 | 특징 | 장점 | 단점 |
|---|---|---|---|
| `snunlp/KR-FinBert-SC` (현재) | 금융 감성 | 한국어 지원 | 도메인 미스매치 |
| `monologg/koelectra-base-finetuned-sentiment` | 일반 한국어 감성 | 일상 대화 적합 | 허깅페이스 가용성 확인 필요 |
| `klue/roberta-base` + 파인튜닝 | KLUE 벤치마크 | 범용 | 파인튜닝 데이터 필요 |
| Claude API 기반 | 프롬프트 분류 | 도메인 무관 정확 | 비용, 지연 |

**Phase 1 결정**: KR-FinBert-SC 유지 + 규칙 기반 보완 강화  
**Phase 2**: `koelectra` 또는 Claude 감정 분류 A/B 테스트

### 1-3. 규칙 기반 보완 강화

현재 `NEGATIVE_WORDS`/`POSITIVE_WORDS` 단순 포함 체크 → 가중치 기반으로 개선:

```python
# emotion.py 수정
EMOTION_PATTERNS = {
    "negative": {
        "high": ["죽고 싶", "사라지고 싶", "포기하고", "살기 싫"],   # 가중치 3
        "medium": ["외롭", "힘들어", "슬프", "지쳐", "아무도 없"],    # 가중치 2
        "low": ["피곤", "귀찮", "모르겠", "그냥"],                     # 가중치 1
    },
    "positive": {
        "high": ["행복해", "즐거웠", "감사해", "기뻐"],               # 가중치 3
        "medium": ["좋았", "고마워", "설레", "신났"],                  # 가중치 2
        "low": ["괜찮", "나쁘지 않", "그럭저럭"],                      # 가중치 1
    }
}

def _rule_based_v2(text: str) -> dict:
    neg_score = sum(
        w * sum(1 for kw in kws if kw in text)
        for w, (level, kws) in [
            (3, ("high", EMOTION_PATTERNS["negative"]["high"])),
            (2, ("medium", EMOTION_PATTERNS["negative"]["medium"])),
            (1, ("low", EMOTION_PATTERNS["negative"]["low"])),
        ]
    )
    pos_score = sum(
        w * sum(1 for kw in kws if kw in text)
        for w, (level, kws) in [
            (3, ("high", EMOTION_PATTERNS["positive"]["high"])),
            (2, ("medium", EMOTION_PATTERNS["positive"]["medium"])),
            (1, ("low", EMOTION_PATTERNS["positive"]["low"])),
        ]
    )
    total = neg_score + pos_score
    if total == 0:
        return {"label": "neutral", "score": 0.55}
    if neg_score > pos_score:
        return {"label": "negative", "score": min(0.5 + neg_score / (total + 4), 0.95)}
    return {"label": "positive", "score": min(0.5 + pos_score / (total + 4), 0.95)}
```

---

## Step 2 — 언어 패턴 분석

**새 파일**: `backend/app/services/language_pattern.py`

### 2-1. TTR (Type-Token Ratio) — 어휘 다양성

```python
import re
from collections import Counter

def calc_ttr(text: str) -> float:
    """
    Type-Token Ratio: 고유 어휘 수 / 전체 어휘 수
    0 ~ 1 범위. 높을수록 어휘 다양성 높음.
    치매 초기: TTR 감소 경향
    """
    # 한국어 형태소 기반 토크나이징 (간소화: 공백+구두점 분리)
    tokens = re.findall(r'[가-힣]+', text)
    if len(tokens) < 3:
        return 1.0  # 너무 짧으면 의미 없음
    return len(set(tokens)) / len(tokens)


def calc_moving_ttr(texts: list[str], window: int = 7) -> list[float]:
    """
    최근 N일 대화의 TTR 이동 평균
    감소 추세 시 언어 능력 저하 신호
    """
    ttrs = [calc_ttr(t) for t in texts]
    if len(ttrs) < window:
        return ttrs
    return [
        sum(ttrs[max(0, i-window):i+1]) / min(window, i+1)
        for i in range(len(ttrs))
    ]
```

### 2-2. 반복 표현 비율 — n-gram 기반

```python
def calc_repetition_ratio(texts: list[str], n: int = 3) -> float:
    """
    n-gram 중복 비율: 전체 n-gram 중 반복된 것의 비율
    높을수록 반복 표현 증가 → 치매 조기 감지 지표
    """
    all_tokens = []
    for text in texts:
        tokens = re.findall(r'[가-힣]+', text)
        all_tokens.extend(tokens)
    
    if len(all_tokens) < n:
        return 0.0
    
    ngrams = [tuple(all_tokens[i:i+n]) for i in range(len(all_tokens)-n+1)]
    counts = Counter(ngrams)
    duplicated = sum(1 for cnt in counts.values() if cnt > 1)
    return duplicated / len(counts) if counts else 0.0


def calc_sentence_length_variance(texts: list[str]) -> float:
    """
    문장 길이 분산: 낮을수록 단조로운 대화 패턴
    치매 조기 신호: 문장 길이 수렴
    """
    lengths = [len(re.findall(r'[가-힣]+', t)) for t in texts if t.strip()]
    if len(lengths) < 2:
        return 0.0
    mean = sum(lengths) / len(lengths)
    variance = sum((l - mean) ** 2 for l in lengths) / len(lengths)
    return variance
```

---

## Step 3 — 참여 패턴 분석

**파일**: `backend/app/services/alert.py` 또는 새 `participation_pattern.py`

### 3-1. 일별 접속 빈도 분석

```python
async def analyze_participation(db: AsyncSession, user_id: str, days: int = 30) -> dict:
    """최근 N일 접속 패턴 분석"""
    from datetime import datetime, timedelta, date
    from sqlalchemy import func, cast, Date
    
    cutoff = datetime.utcnow() - timedelta(days=days)
    result = await db.execute(
        select(
            cast(Conversation.created_at, Date).label("day"),
            func.count(Conversation.id).label("msg_count"),
        )
        .where(
            Conversation.user_id == uuid.UUID(user_id),
            Conversation.role == "user",
            Conversation.created_at >= cutoff,
        )
        .group_by(cast(Conversation.created_at, Date))
        .order_by(cast(Conversation.created_at, Date))
    )
    rows = result.all()
    
    active_days = len(rows)
    total_messages = sum(r.msg_count for r in rows)
    
    # 연속 미접속 최대 일수
    if rows:
        sorted_days = sorted([r.day for r in rows])
        max_gap = 0
        for i in range(1, len(sorted_days)):
            gap = (sorted_days[i] - sorted_days[i-1]).days - 1
            max_gap = max(max_gap, gap)
    else:
        max_gap = days
    
    return {
        "active_days": active_days,
        "total_messages": total_messages,
        "avg_messages_per_active_day": total_messages / active_days if active_days > 0 else 0,
        "max_consecutive_absence": max_gap,
        "participation_rate": active_days / days,
    }
```

### 3-2. 대화 길이 변화 추이

```python
async def analyze_message_length_trend(db: AsyncSession, user_id: str, days: int = 14) -> dict:
    """최근 대화 길이 변화 (감소 추세 = 우울/참여 저하 신호)"""
    from datetime import datetime, timedelta
    
    cutoff = datetime.utcnow() - timedelta(days=days)
    result = await db.execute(
        select(Conversation.content, Conversation.created_at)
        .where(
            Conversation.user_id == uuid.UUID(user_id),
            Conversation.role == "user",
            Conversation.created_at >= cutoff,
        )
        .order_by(Conversation.created_at)
    )
    rows = result.all()
    
    if len(rows) < 3:
        return {"trend": "insufficient_data", "slope": 0}
    
    lengths = [len(r.content) for r in rows]
    # 선형 회귀 기울기 (간소화)
    n = len(lengths)
    x_mean = (n - 1) / 2
    y_mean = sum(lengths) / n
    numerator = sum((i - x_mean) * (lengths[i] - y_mean) for i in range(n))
    denominator = sum((i - x_mean) ** 2 for i in range(n))
    slope = numerator / denominator if denominator != 0 else 0
    
    if slope < -2:
        trend = "decreasing"
    elif slope > 2:
        trend = "increasing"
    else:
        trend = "stable"
    
    return {"trend": trend, "slope": round(slope, 2), "avg_length": round(y_mean, 1)}
```

---

## Step 4 — 5개 심리 지수 집계

**새 파일**: `backend/app/services/psych_index.py`

### 4-1. 5개 지수 정의

| 지수 | 측정 방법 | 범위 |
|---|---|---|
| **외로움** | 부정 감정 빈도 + 접속 빈도 역수 | 0~100 (높을수록 외로움) |
| **활력** | 긍정 감정 빈도 + 메시지 길이 정규화 | 0~100 |
| **인지** | TTR + 반복 표현 비율 역수 | 0~100 |
| **관계** | 대화 주제 다양성 (미래 확장) | 0~100 |
| **미래** | 미래 지향적 발화 비율 | 0~100 |

```python
async def compute_psych_indices(
    db: AsyncSession,
    user_id: str,
    days: int = 7,
) -> dict:
    """5개 심리 지수 계산"""
    from app.services.alert import get_recent_emotions
    from app.services.language_pattern import calc_ttr, calc_repetition_ratio
    
    emotions = await get_recent_emotions(db, user_id, days)
    participation = await analyze_participation(db, user_id, days)
    
    # 최근 대화 텍스트 수집
    cutoff = datetime.utcnow() - timedelta(days=days)
    text_result = await db.execute(
        select(Conversation.content)
        .where(
            Conversation.user_id == uuid.UUID(user_id),
            Conversation.role == "user",
            Conversation.created_at >= cutoff,
        )
        .order_by(Conversation.created_at)
    )
    texts = [r[0] for r in text_result.all()]
    
    # 감정 비율
    total_emo = len(emotions)
    neg_ratio = sum(1 for e in emotions if e["label"] == "negative") / total_emo if total_emo > 0 else 0.5
    pos_ratio = sum(1 for e in emotions if e["label"] == "positive") / total_emo if total_emo > 0 else 0.5
    
    # 언어 패턴
    all_text = " ".join(texts)
    ttr = calc_ttr(all_text) if all_text else 0.5
    rep = calc_repetition_ratio(texts) if texts else 0.0
    
    # 외로움 지수 (0~100, 높을수록 외로움)
    loneliness = round(
        neg_ratio * 50
        + (1 - participation["participation_rate"]) * 30
        + max(0, participation["max_consecutive_absence"] - 2) * 5
    , 1)
    loneliness = min(100, loneliness)
    
    # 활력 지수
    vitality = round(pos_ratio * 60 + participation["participation_rate"] * 40, 1)
    vitality = min(100, vitality)
    
    # 인지 지수 (TTR 높고 반복 낮을수록 좋음)
    cognition = round((ttr * 60) + (1 - min(rep, 1)) * 40, 1)
    cognition = min(100, cognition)
    
    # 관계 지수 (현재: 참여율 기반, 추후 주제 다양성 반영)
    relationship = round(participation["participation_rate"] * 100, 1)
    
    # 미래 지수 (미래 지향 키워드 기반)
    FUTURE_KEYWORDS = ["내년", "다음에", "나중에", "앞으로", "계획", "하고 싶", "기대"]
    future_mentions = sum(1 for t in texts for kw in FUTURE_KEYWORDS if kw in t)
    future_index = round(min(future_mentions * 10, 100), 1)
    
    return {
        "loneliness": loneliness,
        "vitality": vitality,
        "cognition": cognition,
        "relationship": relationship,
        "future": future_index,
        "meta": {
            "days_analyzed": days,
            "message_count": len(texts),
            "ttr": round(ttr, 3),
            "repetition_ratio": round(rep, 3),
            "participation_rate": round(participation["participation_rate"], 2),
        }
    }
```

---

## Step 5 — 복지사 대시보드 연동

**파일**: `backend/app/routers/welfare.py`

### 사용자 상세 API에 심리 지수 추가

```python
# user_detail() 함수에 추가
from app.services.psych_index import compute_psych_indices

psych = await compute_psych_indices(db, user_id, days=7)

return {
    ...기존 필드...,
    "psych_indices": psych,
    "language_trend": length_trend,
}
```

### 위험도 판정 로직 고도화

현재 `welfare.py`의 단순 판정 (최신 감정만) → 복합 조건으로 고도화:

```python
# 기존
if no_contact or active_alerts > 0:
    level = "red"
elif latest_emotion == "negative":
    level = "yellow"
else:
    level = "green"

# 개선
async def compute_risk_level(
    no_contact: bool,
    active_alerts: int,
    recent_emotions: list[dict],
    participation_rate: float,
) -> str:
    from app.services.emotion import check_emotion_trend
    
    # 긴급: 접속 단절 + 알림 미해결
    if no_contact and active_alerts > 0:
        return "red"
    
    # 긴급: 감정 추세 악화 (연속 3회 부정)
    trend = await check_emotion_trend(recent_emotions)
    if trend == "red":
        return "red"
    
    # 주의: 접속 단절 OR 감정 악화 OR 참여율 급감
    if no_contact or trend == "yellow" or participation_rate < 0.2:
        return "yellow"
    
    return "green"
```

---

## 새 DB 테이블 — psych_indices

```sql
CREATE TABLE IF NOT EXISTS psych_indices (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    user_id UUID NOT NULL REFERENCES users(id) ON DELETE CASCADE,
    computed_at TIMESTAMP DEFAULT NOW(),
    loneliness FLOAT,
    vitality FLOAT,
    cognition FLOAT,
    relationship FLOAT,
    future_index FLOAT,
    ttr FLOAT,
    repetition_ratio FLOAT,
    participation_rate FLOAT
);
CREATE INDEX ON psych_indices (user_id, computed_at);
```

---

## 변경 파일 요약

| 파일 | 변경 내용 | 우선순위 |
|---|---|---|
| `backend/app/services/emotion.py` | 규칙 기반 보완 강화 (가중치 패턴) | 🟡 |
| `backend/app/services/language_pattern.py` | 신규 — TTR, n-gram, 문장 길이 | 🟡 |
| `backend/app/services/psych_index.py` | 신규 — 5개 심리 지수 | 🟡 |
| `backend/app/routers/welfare.py` | 심리 지수 조회, 위험도 복합 판정 | 🟡 |
| `backend/app/init.sql` | `psych_indices` 테이블 추가 | 🟡 |

---

## 테스트 시나리오

1. **TTR**: 반복 문장 ("좋아요 좋아요 좋아요") → TTR 낮음 확인
2. **n-gram 반복**: 같은 표현 여러 번 포함된 텍스트 → 높은 repetition_ratio
3. **5개 지수**: 14일 대화 데이터 입력 후 각 지수 0~100 범위 확인
4. **위험도 복합 판정**: 3일 미접속 + 부정 감정 연속 → red 판정 확인
5. **모델 비교**: KR-FinBert-SC vs 규칙 기반 폴백으로 동일 텍스트 결과 비교

---

> **다음 파이프라인**: E — 안전 감지 (APScheduler, 이메일, 1393)
