"""선택형 응답 → MBTI 성향 집계 유틸.

발행된 설문지(question_set)는 weekly_topics.choices(JSON)에 저장되고,
각 선택형 보기에는 mbti_axis/mbti_pole 태그가 붙어 있다(question_parser.ChoiceOption).
survey_responses는 (question_id, selected_option_id)를 저장하므로,
보기 태그와 응답을 조인하면 응답 테이블 변경 없이 성향을 집계할 수 있다.
"""
from __future__ import annotations

import json
from typing import Iterable

# (axis, 왼쪽 극, 오른쪽 극, 왼쪽 라벨, 오른쪽 라벨)
AXES: list[tuple[str, str, str, str, str]] = [
    ("EI", "E", "I", "외향(E)", "내향(I)"),
    ("SN", "S", "N", "감각(S)", "직관(N)"),
    ("TF", "T", "F", "사고(T)", "감정(F)"),
    ("JP", "J", "P", "판단(J)", "인식(P)"),
]
VALID_POLES = set("EISNTFJP")


def build_option_pole_map(choices_json) -> dict[tuple[str, str], str]:
    """(question_id, option_id) -> pole 매핑. choices_json = topic.choices (JSON str | dict | None)."""
    if not choices_json:
        return {}
    try:
        data = choices_json if isinstance(choices_json, dict) else json.loads(choices_json)
    except Exception:
        return {}
    if not isinstance(data, dict):
        return {}
    mapping: dict[tuple[str, str], str] = {}
    for q in data.get("questions", []) or []:
        q_id = q.get("id")
        for opt in (q.get("options") or []):
            pole = opt.get("mbti_pole")
            opt_id = opt.get("id")
            if q_id and opt_id and pole in VALID_POLES:
                mapping[(q_id, opt_id)] = pole
    return mapping


def tally_poles(
    responses: Iterable[tuple[str, str]],
    pole_map: dict[tuple[str, str], str],
) -> dict[str, int]:
    """responses: (question_id, selected_option_id) 반복자. pole별 카운트 반환."""
    counts = {p: 0 for p in VALID_POLES}
    for q_id, opt_id in responses:
        if not opt_id:
            continue
        pole = pole_map.get((q_id, opt_id))
        if pole:
            counts[pole] += 1
    return counts


def summarize(counts: dict[str, int]) -> dict:
    """pole 카운트 → MBTI 요약(유형 문자열 + 축별 분포 + 신호 수)."""
    axes_out = []
    type_chars = []
    total = 0
    for axis, left, right, left_lab, right_lab in AXES:
        lc = counts.get(left, 0)
        rc = counts.get(right, 0)
        total += lc + rc
        denom = lc + rc
        if denom == 0:
            dominant = None
            type_chars.append("-")
            strength = 0
        else:
            if lc >= rc:
                dominant = left
                type_chars.append(left)
            else:
                dominant = right
                type_chars.append(right)
            strength = round(max(lc, rc) * 100 / denom)
        axes_out.append({
            "axis": axis,
            "left": left, "right": right,
            "left_label": left_lab, "right_label": right_lab,
            "left_count": lc, "right_count": rc,
            "dominant": dominant, "strength": strength,
        })
    return {
        "type": "".join(type_chars),
        "is_complete": "-" not in type_chars,
        "axes": axes_out,
        "total_signals": total,
    }


def short_label(summary: dict) -> str:
    """프롬프트용 한 줄 라벨. 예: 'ENFP 경향' / 'E_F_ 경향(일부)' / '' (신호 없음)."""
    if not summary or summary.get("total_signals", 0) == 0:
        return ""
    t = summary.get("type", "----")
    if summary.get("is_complete"):
        return f"{t} 경향"
    return f"{t} 경향(일부 축만 추정됨)"
