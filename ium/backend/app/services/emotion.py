"""
KoBERT 기반 감정 분석 서비스.
모델 로딩은 시작 시 1회만 수행하며, 추론은 동기 함수로 처리.
"""
from __future__ import annotations
import asyncio
from functools import lru_cache
from typing import TYPE_CHECKING

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
        # 모델 없을 때는 규칙 기반 폴백 사용
        print(f"[emotion] 모델 로드 실패, 규칙 기반 폴백 사용: {e}")


NEGATIVE_WORDS = ["힘들", "외롭", "슬프", "무섭", "지쳐", "죽", "사라", "포기", "아무도"]
POSITIVE_WORDS = ["좋았", "행복", "즐거", "감사", "기뻤", "설레", "신났", "고마"]


def _rule_based(text: str) -> dict:
    neg = sum(1 for w in NEGATIVE_WORDS if w in text)
    pos = sum(1 for w in POSITIVE_WORDS if w in text)
    if neg > pos:
        return {"label": "negative", "score": 0.6 + min(neg * 0.05, 0.3)}
    if pos > neg:
        return {"label": "positive", "score": 0.6 + min(pos * 0.05, 0.3)}
    return {"label": "neutral", "score": 0.55}


def _infer(text: str) -> dict:
    if _model is None:
        return _rule_based(text)
    try:
        import torch
        inputs = _tokenizer(text, return_tensors="pt", truncation=True, max_length=512)
        with torch.no_grad():
            logits = _model(**inputs).logits
        probs = torch.softmax(logits, dim=-1)[0].tolist()
        idx = probs.index(max(probs))
        return {"label": LABELS[idx], "score": probs[idx]}
    except Exception:
        return _rule_based(text)


async def analyze(text: str) -> dict:
    loop = asyncio.get_event_loop()
    return await loop.run_in_executor(None, _infer, text)


async def check_emotion_trend(recent_emotions: list[dict]) -> str | None:
    """최근 감정 리스트 기반 경보 수준 반환"""
    if len(recent_emotions) < 3:
        return None
    neg_count = sum(1 for e in recent_emotions if e.get("label") == "negative")
    last_three_all_neg = all(e.get("label") == "negative" for e in recent_emotions[-3:])

    if last_three_all_neg and neg_count >= 5:
        return "red"
    if neg_count >= 5:
        return "yellow"
    return None


# 앱 시작 시 백그라운드에서 로드
def preload():
    _load_model()
