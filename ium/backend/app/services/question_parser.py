# backend/app/services/question_parser.py
# Pydantic 모델 정의 (instructor 연동용 단일 진실 공급원)
# Python 3.10+ (Union 대신 | 문법)

from typing import Literal, List, Optional
from pydantic import BaseModel, model_validator


class ChoiceOption(BaseModel):
    id: str
    label: str
    value: str
    icon_hint: Optional[str] = None
    is_other: bool = False
    # MBTI 유추용 태그 — 이 보기를 고른 사용자가 어느 성향으로 기우는지.
    # 향수를 자극하는 보기 문구는 그대로 두고, 성향 정보는 이 메타데이터에만 담는다.
    # axis: EI(외향/내향) | SN(감각/직관) | TF(사고/감정) | JP(판단/인식)
    # pole: E | I | S | N | T | F | J | P  ('그 외' 같은 열린 창 보기는 태깅하지 않음)
    mbti_axis: Optional[Literal["EI", "SN", "TF", "JP"]] = None
    mbti_pole: Optional[Literal["E", "I", "S", "N", "T", "F", "J", "P"]] = None


class QuestionItem(BaseModel):
    id: str
    type: Literal["choice", "narrative"]
    text: str
    target_age: Literal["elderly", "youth", "both"] = "both"
    allow_multiple: bool = False
    max_selections: int = 1
    has_other: bool = False
    options: Optional[List[ChoiceOption]] = None
    guidelines: Optional[List[str]] = None
    placeholder: Optional[str] = None
    min_length_hint: Optional[str] = None
    suggested_duration_seconds: Optional[int] = None  # narrative 전용


class ImageAnalysis(BaseModel):
    """유물 분석 결과 — 복지사 주제 선택용 (0609 설계: artifact 중심)"""
    artifact_summary: dict
    context: dict
    mood: dict
    topic_candidates: list[dict]


class QuestionSet(BaseModel):
    schema_version: Literal["1.0"] = "1.0"
    question_type: Literal["choice", "narrative", "mixed"]
    questions: List[QuestionItem]

    @model_validator(mode="after")
    def validate_mixed_structure(self):
        if self.question_type == "mixed":
            if not self.questions:
                raise ValueError("mixed 타입은 최소 1개의 질문이 필요합니다.")
            # mixed: choice 질문들이 먼저, 그 다음 narrative 질문들
            # choice→narrative 순서로 전환된 이후에는 narrative만 허용
            seen_narrative = False
            for q in self.questions:
                if q.type == "narrative":
                    seen_narrative = True
                elif q.type == "choice" and seen_narrative:
                    raise ValueError("mixed 타입은 choice 질문 후에 narrative가 와야 합니다. choice는 narrative 앞에만 올 수 있습니다.")
            if not any(q.type == "choice" for q in self.questions):
                raise ValueError("mixed 타입은 최소 1개의 choice 질문이 필요합니다.")
        return self


import re

PROHIBITED_PATTERNS = [
    (r"기분.*어땠", "정서 직접 묻기"),
    (r"그립.*나요", "정서 직접 묻기"),
    (r"외로.*우셨", "정서 직접 묻기"),
    (r"가장.*기억에 남는", "최고급 강요"),
    (r"가장.*좋았던", "최고급 강요"),
    (r"가장.*행복했던", "최고급 강요"),
    (r"가장.*감동", "최고급 강요"),
    (r"해 주세요$", "명령형 압박"),
    (r"말씀해 주세요", "명령형 압박"),
    (r"이야기해 주세요", "명령형 압박"),
    (r"기타$", "열린 선택지 미사용"),
]


def validate_question_quality(question_set: "QuestionSet") -> list[str]:
    """금지 패턴 감지. 위반 문구 목록 반환 (빈 list = 통과)."""
    violations: list[str] = []
    for q in question_set.questions:
        for pattern, category in PROHIBITED_PATTERNS:
            if re.search(pattern, q.text):
                violations.append(f"[{q.id}] {category}: '{q.text}'")
        if q.options:
            for opt in q.options:
                if opt.label == "기타":
                    violations.append(f"[{q.id}] 열린 선택지 미사용: 보기 '{opt.label}'")
    return violations


# 폴백 상수 — AI 실패 또는 API 키 없을 때 사용
DEFAULT_FALLBACK: QuestionSet = QuestionSet(
    question_type="narrative",
    questions=[
        QuestionItem(
            id="q1",
            type="narrative",
            text="오늘 어떤 이야기를 나눠 보고 싶으신가요?",
            target_age="both",
            placeholder="자유롭게 이야기해 주세요...",
            guidelines=["오늘 하루 기억에 남는 일", "요즘 관심 있는 것"],
        )
    ],
)
