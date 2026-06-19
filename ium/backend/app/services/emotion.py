"""
KoBERT 기반 감정 분석 서비스.
모델 로딩은 시작 시 1회만 수행하며, 추론은 동기 함수로 처리.
"""
from __future__ import annotations
import asyncio

LABELS = ["negative", "neutral", "positive"]

_model = None
_tokenizer = None


def _load_model():
    global _model, _tokenizer
    if _model is not None:
        return
    try:
        from transformers import AutoTokenizer, AutoModelForSequenceClassification
        import torch

        model_name = "snunlp/KR-FinBert-SC"
        _tokenizer = AutoTokenizer.from_pretrained(model_name)
        _model = AutoModelForSequenceClassification.from_pretrained(model_name)
        _model.eval()
    except Exception as e:
        print(f"[emotion] 모델 로드 실패, 규칙 기반 폴백 사용: {e}")


# 가중치 기반 감정 패턴 (C-1)
EMOTION_PATTERNS = {
    "high_negative": {
        "keywords": ["죽고 싶", "살기 싫", "자해", "없어지고 싶", "끝내고 싶"],
        "weight": 3,
    },
    "medium_negative": {
        "keywords": ["힘들어", "외로워", "무서워", "슬퍼", "괴로워", "우울해", "지쳐"],
        "weight": 2,
    },
    "low_negative": {
        "keywords": ["피곤", "걱정", "불안", "귀찮", "싫어", "짜증"],
        "weight": 1,
    },
    "high_positive": {
        "keywords": ["행복해", "너무 좋아", "기뻐", "설레", "신나"],
        "weight": 3,
    },
    "medium_positive": {
        "keywords": ["좋아", "감사", "즐거워", "고마워", "뿌듯"],
        "weight": 2,
    },
    "low_positive": {
        "keywords": ["괜찮아", "나쁘지 않아", "좋았", "웃겨"],
        "weight": 1,
    },
}


def _weighted_score(text: str) -> dict:
    neg_score = 0
    pos_score = 0
    for pattern_type, pattern in EMOTION_PATTERNS.items():
        for kw in pattern["keywords"]:
            if kw in text:
                if "negative" in pattern_type:
                    neg_score += pattern["weight"]
                else:
                    pos_score += pattern["weight"]

    total = neg_score + pos_score
    if total == 0:
        return {"label": "neutral", "score": 0.55}
    if neg_score > pos_score:
        return {"label": "negative", "score": min(0.5 + neg_score * 0.08, 0.95)}
    return {"label": "positive", "score": min(0.5 + pos_score * 0.08, 0.95)}


def _infer(text: str) -> dict:
    if _model is None:
        return _weighted_score(text)
    try:
        import torch
        inputs = _tokenizer(text, return_tensors="pt", truncation=True, max_length=512)
        with torch.no_grad():
            logits = _model(**inputs).logits
        probs = torch.softmax(logits, dim=-1)[0].tolist()
        idx = probs.index(max(probs))
        return {"label": LABELS[idx], "score": probs[idx]}
    except Exception:
        return _weighted_score(text)


def get_crisis_level(text: str) -> str | None:
    """고위험 키워드 직접 감지 — 모델 추론과 별개로 동작"""
    for kw in EMOTION_PATTERNS["high_negative"]["keywords"]:
        if kw in text:
            return "red"
    return None


async def analyze(text: str) -> dict:
    loop = asyncio.get_event_loop()
    return await loop.run_in_executor(None, _infer, text)


async def check_emotion_trend(recent_emotions: list[dict]) -> str | None:
    if len(recent_emotions) < 3:
        return None
    neg_count = sum(1 for e in recent_emotions if e.get("label") == "negative")
    last_three_all_neg = all(e.get("label") == "negative" for e in recent_emotions[-3:])

    if last_three_all_neg and neg_count >= 5:
        return "red"
    if neg_count >= 5:
        return "yellow"
    return None


def preload():
    _load_model()
