"""언어 패턴 분석 — TTR, n-gram 반복, 문장 길이 분산 (C-2)"""
from __future__ import annotations
import re
import statistics


def _tokenize(text: str) -> list[str]:
    return [t for t in re.split(r"\s+", text.strip()) if t]


def _split_sentences(text: str) -> list[str]:
    return [s.strip() for s in re.split(r"[.!?。]+", text) if s.strip()]


def calc_ttr(text: str) -> float:
    """어휘 다양성: 고유 어절 수 / 전체 어절 수 (0~1, 높을수록 다양)"""
    tokens = _tokenize(text)
    if not tokens:
        return 0.0
    return len(set(tokens)) / len(tokens)


def calc_ngram_repetition(text: str, n: int = 2) -> float:
    """n-gram 반복 비율: 중복 n-gram / 전체 n-gram (0~1, 낮을수록 다양)"""
    tokens = _tokenize(text)
    if len(tokens) < n:
        return 0.0
    ngrams = [tuple(tokens[i:i + n]) for i in range(len(tokens) - n + 1)]
    if not ngrams:
        return 0.0
    unique = len(set(ngrams))
    repeated = len(ngrams) - unique
    return repeated / len(ngrams)


def calc_sentence_length_variance(text: str) -> float:
    """문장 길이 분산 (어절 기준, 높을수록 문장 구조 다양)"""
    sentences = _split_sentences(text)
    lengths = [len(_tokenize(s)) for s in sentences if _tokenize(s)]
    if len(lengths) < 2:
        return 0.0
    return statistics.variance(lengths)


def analyze_text(text: str) -> dict:
    """3개 지표 한번에 반환"""
    return {
        "ttr": round(calc_ttr(text), 4),
        "ngram_repetition": round(calc_ngram_repetition(text), 4),
        "sentence_length_variance": round(calc_sentence_length_variance(text), 4),
    }
