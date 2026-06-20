# -*- coding: utf-8 -*-
"""
v5 증거 연결: 신규 부모 구성개념 + 신규 trait 인과.
 - initiating_structure(Ohio, Judge 2004) → T01·T06·T10 (과업축 공유부모; 통합은 데이터 보류)
 - ambidextrous(Rosing 2011) → T12 (Balanced 재정의·구제)
 - empowering → T15, abusive_supervision → T107 매핑 + 인과
실행: python -X utf8 scripts/build_v5_evidence.py
"""
import json
import os
from datetime import date

BASE = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
REG = os.path.join(BASE, "data/evidence/leadership_evidence_registry.json")
CAU = os.path.join(BASE, "data/evidence/causal_rationale.json")
TODAY = date.today().isoformat()

NEW_CONSTRUCTS = [
    {"id": "initiating_structure", "name_ko": "과업구조화(Ohio Initiating Structure)", "polarity": "positive",
     "mapped_traits": ["T01", "T06", "T10"], "validity_status": "established", "attention_trend": "stable",
     "first_seen_year": 1957, "incremental_validity": "Initiating Structure ρ=.29 (Judge 2004 메타)",
     "implication": "keep",
     "trend_note": "Ohio State 2요인 중 과업축. T01·T06·T10이 *공유하는 부모* → 이 셋은 과업축 중복 클러스터. 통합 여부는 요인분석(데이터)으로 결정, 현재는 공유부모로 명시하고 통합 보류.",
     "sources": [{"cite": "Judge, Piccolo & Ilies, The Forgotten Ones (consideration & initiating structure 메타)",
                  "year": 2004, "type": "meta-analysis",
                  "url": "https://psycnet.apa.org/doi/10.1037/0021-9010.89.1.36",
                  "doi": "10.1037/0021-9010.89.1.36", "evidence_grade": "M", "peer_reviewed": True,
                  "claim_quote": "Initiating Structure ρ=.29, Consideration ρ=.48 (JAP 89:36-51)"}],
     "last_reviewed": TODAY},
    {"id": "ambidextrous", "name_ko": "양손잡이(탐색-활용) 리더십", "polarity": "positive",
     "mapped_traits": ["T12"], "validity_status": "growing", "attention_trend": "rising",
     "first_seen_year": 2011, "incremental_validity": "opening/closing 전환이 혁신 촉진(Rosing 2011)",
     "implication": "keep",
     "trend_note": "T12 Balanced를 *ambidextrous(탐색-활용 균형)*로 재정의·구제. opening(탐색 촉진)+closing(활용·정렬) 행동을 상황에 맞게 유연 전환. '특색없는 residual'이 아니라 균형 전환이 핵심.",
     "sources": [{"cite": "Rosing, Frese & Bausch, Ambidextrous Leadership (Leadership Quarterly)",
                  "year": 2011, "type": "primary",
                  "url": "https://www.sciencedirect.com/science/article/abs/pii/S1048984311001019",
                  "doi": "10.1016/j.leaqua.2011.07.014", "evidence_grade": "E", "peer_reviewed": True,
                  "claim_quote": "opening·closing 행동 전환이 리더십-혁신 관계의 이질성 설명(LQ 22:956-974)"}],
     "last_reviewed": TODAY},
]

NEW_CAUSAL = {
    "initiating_structure": {
        "dimensions": ["Initiating Structure(과업 구조화)", "역할·기대 명확화", "성과 모니터링"],
        "dimensions_source": {"cite": "Judge et al. (JAP)", "url": "https://psycnet.apa.org/doi/10.1037/0021-9010.89.1.36",
                              "doi": "10.1037/0021-9010.89.1.36", "evidence_grade": "M", "peer_reviewed": True},
        "trait_links": [
            {"trait": "T01", "instantiates": "Initiating Structure(방향·구조 제시)",
             "why": "목표 기반의 명확한 결정과 구조 부여 = 과업 구조화", "causal_grade": "수렴근거",
             "rival": "독단(N19-01)과 표면 유사", "disconfirm": "구조화가 일방 통제로 기능하면 IS 아님",
             "key_micros": [{"id": "M36-01", "why": "전략적 결단이 과업 구조화의 변별 행동(앵커)"}, {"id": "M01-01", "why": "명확한 방향 제시"}]},
            {"trait": "T06", "instantiates": "Initiating Structure(실행 추진·모니터링)",
             "why": "실행을 추진하고 성과를 모니터링 = 과업 구조화의 실행 측면", "causal_grade": "수렴근거",
             "rival": "과도 통제(N24-01)와 표면 유사", "disconfirm": "성과 압박이 학대 동반 시 IS 아님",
             "key_micros": [{"id": "M44-02", "why": "성취지향 실행이 변별 행동(앵커)"}, {"id": "M10-01", "why": "실행 추진"}]},
            {"trait": "T10", "instantiates": "Initiating Structure(전략→실행 구조화)",
             "why": "전략적 자원배분과 실행 구조화", "causal_grade": "논쟁",
             "rival": "T01·T06과 중복(과업축)", "disconfirm": "고유 변별이 없으면 별도 trait 불성립 → 통합 후보(요인분석 필요)",
             "key_micros": [{"id": "M27-01", "why": "전략적 자원배분이 변별 행동(앵커)"}, {"id": "M10-02", "why": "실행 완수"}]},
        ],
        "note": "T01·T06·T10은 Initiating Structure를 공유 = 과업축 중복 클러스터. 통합/유지는 수렴·변별 타당도(요인분석=데이터)로 결정. 현재는 공유부모 명시로 구성타당도 백로그를 *가시화*만.",
    },
    "ambidextrous": {
        "dimensions": ["Opening behaviors(탐색 촉진)", "Closing behaviors(활용·정렬)", "유연한 전환"],
        "dimensions_source": {"cite": "Rosing et al. (LQ)", "url": "https://www.sciencedirect.com/science/article/abs/pii/S1048984311001019",
                              "doi": "10.1016/j.leaqua.2011.07.014", "evidence_grade": "E", "peer_reviewed": True},
        "trait_links": [
            {"trait": "T12", "instantiates": "Opening + Closing 균형(탐색-활용 전환)",
             "why": "탐색(혁신 장려)과 활용(운영 안정·정렬)을 상황에 맞게 균형 = ambidextrous", "causal_grade": "수렴근거",
             "rival": "특색 없는 residual(평균)로 보일 수 있음", "disconfirm": "탐색·활용 전환 행동이 관측되지 않고 단순 중간값이면 ambidextrous 아님(폐기 대상)",
             "key_micros": [{"id": "M24-01", "why": "운영 안정 = closing(활용) 행동"}, {"id": "M28-01", "why": "정보 공유 = 정렬"}]},
        ],
    },
    "empowering": {
        "dimensions": ["Delegation(위임)", "Autonomy Support(자율 지원)", "Coaching/Information-sharing"],
        "dimensions_source": {"cite": "Lee et al. empowering meta", "url": "https://onlinelibrary.wiley.com/doi/abs/10.1002/job.2220",
                              "doi": "10.1002/job.2220", "evidence_grade": "M", "peer_reviewed": True},
        "trait_links": [
            {"trait": "T15", "instantiates": "Delegation + Autonomy Support",
             "why": "권한 이양·자율 부여로 심리적 임파워먼트 유발 = 임파워링 핵심", "causal_grade": "수렴근거",
             "rival": "방임(T101)과 표면 유사 — 둘 다 개입 축소", "disconfirm": "위임이 지원·책임 없이 방치로 기능하면 임파워링 아님(방임)",
             "key_micros": [{"id": "M49-01", "why": "권한 위임이 임파워링의 변별 행동(앵커)"}, {"id": "M49-02", "why": "자율성 부여"}]},
        ],
        "note": "부정 N24(과도통제)·N15-07(과잉보호)의 긍정 대칭축이 T15로 채워짐(비대칭 교정 완료).",
    },
    "abusive_supervision": {
        "dimensions": ["Sustained Hostility(지속적 적대)", "Verbal Abuse(언어적 학대)", "Belittling(비하)"],
        "dimensions_source": {"cite": "Tepper, Consequences of Abusive Supervision (AMJ)", "url": "https://journals.aom.org/doi/abs/10.5465/1556375",
                              "doi": "10.5465/1556375", "evidence_grade": "E", "peer_reviewed": True},
        "trait_links": [
            {"trait": "T107", "instantiates": "Sustained Hostility / Verbal Abuse",
             "why": "지속적 적대·모욕·비하 = 학대적 감독의 핵심", "causal_grade": "이론연역",
             "rival": "일회성 질책·업무 비판과 구분 필요", "disconfirm": "비판이 업무 한정·일회성·건설적이면 학대 아님",
             "key_micros": [{"id": "N40-01", "why": "지속적 적대·모욕이 학대의 변별 행동(앵커)"}]},
        ],
        "note": "Schmidt 5차원 중 abusive supervision을 N15(심리안전파괴)에서 분리해 T107로 독립 → 권위주의(T102 통제)와 학대(T107 적대)의 인과를 구분.",
    },
}

with open(REG, encoding="utf-8") as f:
    reg = json.load(f)
ids = {c["id"] for c in reg["constructs"]}
for nc in NEW_CONSTRUCTS:
    if nc["id"] not in ids:
        reg["constructs"].append(nc)
for c in reg["constructs"]:
    if c["id"] == "empowering":
        c["mapped_traits"] = ["T15"]
        c["implication"] = "keep"
    if c["id"] == "abusive_supervision":
        c["mapped_traits"] = ["T107"]
        c["implication"] = "keep"
with open(REG, "w", encoding="utf-8") as f:
    json.dump(reg, f, ensure_ascii=False, indent=2)

with open(CAU, encoding="utf-8") as f:
    cau = json.load(f)
for cid, entry in NEW_CAUSAL.items():
    cau["constructs"][cid] = entry
with open(CAU, "w", encoding="utf-8") as f:
    json.dump(cau, f, ensure_ascii=False, indent=2)

print("v5 증거 연결 완료: initiating_structure·ambidextrous 추가, empowering→T15·abusive→T107 인과 연결")
