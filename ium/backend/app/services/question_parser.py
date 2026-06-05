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
