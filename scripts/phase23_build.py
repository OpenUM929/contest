# -*- coding: utf-8 -*-
"""
Phase2(비파괴)+Phase3 빌드:
 - 신규 부모 구성개념 participative(T02), behavioral_integrity(T103) 추가 (레지스트리+causal)
 - abusive_supervision에 Tepper(2000) 1차 출처 추가
 - 기존+신규 인과 trait_link에 Phase3 필드(rival/disconfirm/causal_grade) 부착
모두 append/필드추가만(기존 trait 통합·폐기 없음).
실행: python -X utf8 scripts/phase23_build.py
"""
import json
import os
from datetime import date

BASE = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
REG = os.path.join(BASE, "data/evidence/leadership_evidence_registry.json")
CAU = os.path.join(BASE, "data/evidence/causal_rationale.json")
TODAY = date.today().isoformat()

# ---------- 신규 레지스트리 구성개념 ----------
NEW_CONSTRUCTS = [
    {
        "id": "participative", "name_ko": "참여적 리더십", "polarity": "positive",
        "mapped_traits": ["T02"], "validity_status": "established", "attention_trend": "stable",
        "first_seen_year": 1971, "incremental_validity": "직무만족·성과에 정효과(임파워먼트 매개)",
        "implication": "keep",
        "trend_note": "협의·공동 의사결정·정보공유(Path-Goal/Yukl consulting). T02 Collaborative의 학술 부모. 참여가 형식적이면 효과 소멸(가짜 참여 주의).",
        "sources": [{"cite": "Xu et al., Threshold effect of participative leadership & info sharing (AMJ)",
                     "year": 2017, "type": "primary",
                     "url": "https://journals.aom.org/doi/10.5465/amj.2013.0427",
                     "doi": "10.5465/amj.2013.0427", "evidence_grade": "E", "peer_reviewed": True,
                     "claim_quote": "참여적 리더십–정보공유–성과 관계의 임계효과(AMJ)"}],
        "last_reviewed": TODAY,
    },
    {
        "id": "behavioral_integrity", "name_ko": "행동적 진실성(위반=T103)", "polarity": "negative",
        "mapped_traits": ["T103"], "validity_status": "established", "attention_trend": "stable",
        "first_seen_year": 2002, "incremental_validity": "말-행동 정렬 지각→신뢰·성과(Simons)",
        "implication": "keep",
        "trend_note": "Simons 행동적 진실성=관리자의 말과 행동 정렬 지각. T103 Integrity Violation은 *그 위반*(언행 불일치·약속 미이행·투명성 위반). 부모 구성개념으로 T103을 정초.",
        "sources": [{"cite": "Simons, Behavioral Integrity (Organization Science)",
                     "year": 2002, "type": "primary",
                     "url": "https://pubsonline.informs.org/doi/10.1287/orsc.13.1.18.543",
                     "doi": "10.1287/orsc.13.1.18.543", "evidence_grade": "E", "peer_reviewed": True,
                     "claim_quote": "말-행동 정렬 지각이 신뢰의 선행(Organization Science 13:18-35)"}],
        "last_reviewed": TODAY,
    },
]

TEPPER_SRC = {"cite": "Tepper, Consequences of Abusive Supervision (AMJ)", "year": 2000,
              "type": "primary", "url": "https://journals.aom.org/doi/abs/10.5465/1556375",
              "doi": "10.5465/1556375", "evidence_grade": "E", "peer_reviewed": True,
              "claim_quote": "학대적 감독→이직의도↑·직무/삶 만족↓·심리적 고통(AMJ 43:178-190)"}

# ---------- 신규 causal 엔트리 ----------
NEW_CAUSAL = {
    "participative": {
        "dimensions": ["Consultation(협의)", "Joint Decision-Making(공동 의사결정)", "Information Sharing(정보 공유)"],
        "dimensions_source": {"cite": "Xu et al. (AMJ)", "url": "https://journals.aom.org/doi/10.5465/amj.2013.0427",
                              "doi": "10.5465/amj.2013.0427", "evidence_grade": "E", "peer_reviewed": True},
        "trait_links": [{
            "trait": "T02", "instantiates": "Consultation + Joint Decision-Making",
            "why": "구성원 의견을 구하고 공동으로 결정 = 참여적 리더십의 핵심 행동",
            "causal_grade": "수렴근거",
            "rival": "협의가 형식적 동의 구하기(가짜 참여)이거나, 결정 회피(방임 T101)일 수 있음",
            "disconfirm": "의견 수렴이 실제 결정에 반영되지 않고 독단(N19-01) 동반 시 참여 인과 무효",
            "key_micros": [{"id": "M11-01", "why": "경청이 협의의 출발 행동"},
                           {"id": "M15-03", "why": "정보 공유가 공동 의사결정의 조건"}],
        }],
    },
    "behavioral_integrity": {
        "dimensions": ["Word-Deed Alignment(말-행동 정렬)", "Promise Keeping(약속 이행)", "Transparency(투명성)"],
        "dimensions_source": {"cite": "Simons (Organization Science)", "url": "https://pubsonline.informs.org/doi/10.1287/orsc.13.1.18.543",
                              "doi": "10.1287/orsc.13.1.18.543", "evidence_grade": "E", "peer_reviewed": True},
        "trait_links": [{
            "trait": "T103", "instantiates": "Word-Deed Misalignment (낮은 행동적 진실성)",
            "why": "말과 행동의 불일치·약속 미이행·정보 은폐 = 행동적 진실성의 위반",
            "causal_grade": "이론연역",
            "rival": "상황 변화로 인한 불가피한 말 바꿈(정직한 수정)일 수 있음",
            "disconfirm": "불일치가 외부 요인으로 설명되고 투명하게 고지되면 integrity 위반 아님",
            "key_micros": [{"id": "N30-01", "why": "언행 불일치가 위반의 직접 행동(앵커)"},
                           {"id": "N28-01", "why": "정보 은폐 = 투명성 위반"},
                           {"id": "N34-01", "why": "데이터 조작 = 진실성 위반의 강한 형태"}],
        }],
    },
}

# ---------- 기존 trait_link Phase3 필드 (construct, trait) -> {rival, disconfirm, causal_grade} ----------
P3 = {
    ("transformational", "T09"): ("비전 발화가 자기과시(N04 개인숭배)일 수 있음", "비전 발화가 추종자 고무 없이 자기홍보로 귀결되면 영감동기 인과 무효", "수렴근거"),
    ("transformational", "T03"): ("변화 발화가 준비없는 강요(N05)일 수 있음", "아이디어 자극이 실험 장려 아닌 처벌(N26) 동반 시 지적자극 무효", "수렴근거"),
    ("transformational", "T07"): ("성장지원이 과잉개입·통제(N24)일 수 있음", "피드백이 발전보다 평가·질책으로 기능하면 개별배려 무효", "수렴근거"),
    ("transactional_contingent_reward", "T06"): ("실행추진이 독단(N19)·압박만일 수 있음", "보상·명확화 없이 압박만이면 거래적 교환(보상) 아님", "논쟁"),
    ("servant", "T07"): ("developing이 후계 통제 수단일 수 있음", "성장지원이 구성원 자율 확대로 이어지지 않으면 서번트 아님", "수렴근거"),
    ("servant", "T11"): ("배려가 과잉보호(N15-07)로 자율 침해할 수 있음", "웰빙케어가 의존 심화·성장기회 차단 동반 시 정서적 치유 아님", "수렴근거"),
    ("authentic", "T13"): ("도덕적 언어가 인상관리(moral licensing)일 수 있음", "언행일치 주장과 실제 행동 불일치(N30) 관측 시 진성 무효", "논쟁"),
    ("ethical", "T13"): ("규범 강화가 권위적 통제(N15-03)일 수 있음", "원칙 강조가 처벌·공개비난으로 기능하면 윤리 아님", "논쟁"),
    ("adaptive", "T14"): ("학습 강조가 실패 은폐(N22) 회피일 수 있음", "실패수용이 책임회피·학습차단(N22-02) 동반 시 적응 아님", "수렴근거"),
    ("adaptive", "T04"): ("위기대응이 평시 과잉통제 전이일 수 있음", "distress 조절이 공포 조장(N18)으로 기능하면 적응 아님", "논쟁"),
    ("digital", "T14"): ("디지털 강조가 도구 남용(N35)·AI 오용(N37)일 수 있음", "기술활용이 인간중심 결여·감시로 기능하면 디지털리더십 아님", "논쟁"),
    ("toxic_destructive", "T102"): ("강한 방향제시(T01)와 표면 유사", "공개비난·독단이 협의·존중 동반 시 권위주의 아님", "이론연역"),
    ("toxic_destructive", "T104"): ("자기확신(T01)과 표면 유사", "개인숭배 유도가 구성원 공로 인정 동반 시 자기애 아님", "이론연역"),
    ("toxic_destructive", "T106"): ("유연성(T14 적응)과 표면 유사", "비일관성이 맥락 적응의 결과이면 변덕 아님", "수렴근거"),
    ("laissez_faire", "T101"): ("위임(임파워링)과 표면 유사", "개입 축소가 자율부여+지원 동반 시 방임 아님(임파워링)", "이론연역"),
    ("dark_triad", "T104"): ("자기확신과 표면 유사", "개인숭배가 공로 인정 동반 시 자기애 아님", "이론연역"),
    ("dark_triad", "T105"): ("설득·영향력과 표면 유사", "보상 약속이 실제 이행되면 조작 아님", "이론연역"),
}

# ===== 적용 =====
with open(REG, encoding="utf-8") as f:
    reg = json.load(f)
existing_ids = {c["id"] for c in reg["constructs"]}
for nc in NEW_CONSTRUCTS:
    if nc["id"] not in existing_ids:
        reg["constructs"].append(nc)
for c in reg["constructs"]:
    if c["id"] == "abusive_supervision" and not any(s.get("doi") == TEPPER_SRC["doi"] for s in c["sources"]):
        c["sources"].insert(0, TEPPER_SRC)
        c["mapped_traits"] = c.get("mapped_traits", [])
with open(REG, "w", encoding="utf-8") as f:
    json.dump(reg, f, ensure_ascii=False, indent=2)

with open(CAU, encoding="utf-8") as f:
    cau = json.load(f)
for cid, entry in NEW_CAUSAL.items():
    cau["constructs"][cid] = entry
# Phase3 필드 부착
for cid, c in cau["constructs"].items():
    for tl in c.get("trait_links", []):
        key = (cid, tl["trait"])
        if key in P3 and "rival" not in tl:
            tl["rival"], tl["disconfirm"], tl["causal_grade"] = P3[key]
with open(CAU, "w", encoding="utf-8") as f:
    json.dump(cau, f, ensure_ascii=False, indent=2)

print("Phase2/3 빌드 완료: participative·behavioral_integrity 추가, Tepper 출처, Phase3 필드 부착")
