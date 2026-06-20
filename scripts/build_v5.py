# -*- coding: utf-8 -*-
"""
v5 빌드 (append-only, 비파괴):
 1) 모든 trait에 trait_kind(style/capability/context/risk) 부여 → 분석수준 혼재 해소
    (T05·T08=capability, T04=context, T101~T107=risk, 나머지=style)
 2) 신규 micro: M49-01/02(위임·자율), N40-01(지속적 적대) — 학습데이터는 향후
 3) 신규 trait: T15 Empowering, T107 Risk: Abusive Supervision (각 고유 앵커 보유)
기존 trait/micro 삭제·변경 없음. validate_taxonomy로 무결성 확인.
실행: python -X utf8 scripts/build_v5.py
"""
import json
import os

BASE = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
TRAITS = os.path.join(BASE, "data/traits/trait_definitions_v4.json")
POS = os.path.join(BASE, "dataset/ori/positive_micro_labels_v4.json")
NEG = os.path.join(BASE, "dataset/ori/negative_micro_labels_v4.json")

KIND = {"T04": "context", "T05": "capability", "T08": "capability"}
RISK = {"T101", "T102", "T103", "T104", "T105", "T106", "T107"}

NEW_POS = [
    {"label_id": "M49-01", "label_name": "권한 위임/의사결정 이양", "macro": "L49", "weight": 0.8,
     "definition": "구성원에게 의사결정 권한과 책임을 실질적으로 이양하는 행동",
     "when": "권한 위임, 결정권 이양, 책임 부여 | 예시: '이 건은 당신이 결정해서 진행하세요', '권한을 드릴 테니 주도해 주세요'",
     "not_when": "형식만 위임하고 실제로는 통제; 결정 후 번복; 과거 회상 서술(~했었습니다) 시 제외",
     "context_weight": {"crisis": 0.9, "normal": 1.2, "innovation": 1.2}, "role": "anchor"},
    {"label_id": "M49-02", "label_name": "자율성 부여", "macro": "L49", "weight": 0.7,
     "definition": "업무 방식·속도를 구성원이 스스로 정하도록 자율을 보장하는 행동",
     "when": "자율 보장, 방식 자율, 마이크로매니징 지양 | 예시: '방법은 자유롭게 정하세요', '과정은 믿고 맡기겠습니다'",
     "not_when": "세부 단계까지 지시; 자율 표방하나 수시 개입; 과거 회상 서술 시 제외",
     "context_weight": {"crisis": 0.8, "normal": 1.2, "innovation": 1.3}, "role": "discriminative"},
]
NEW_NEG = [
    {"label_id": "N40-01", "label_name": "지속적 적대/모욕", "macro": "N40", "penalty": 0.6, "weight": 0.7,
     "definition": "구성원에게 지속적으로 적대적 언사·모욕·비하를 가하는 행동(학대적 감독)",
     "when": "반복적 모욕·인격 비하·적대적 언사 | 예시: '넌 늘 이 모양이야', '쓸모가 없네' 반복적 폭언",
     "not_when": "일회성 질책; 업무에 한정된 건설적 비판; 과거 시제 키워드 포함 시 트리거 안 함",
     "context_weight": {"crisis": 1.0, "normal": 1.1, "innovation": 1.0}, "role": "anchor"},
]

NEW_TRAITS = [
    {"trait_id": "T15", "trait_type": "positive", "trait_kind": "style", "trait_name": "Empowering Leader",
     "required": ["M49-01", "M49-02"], "optional": ["M27-01", "M02-02"],
     "hard_forbidden": ["N24-01", "N15-07"], "soft_forbidden": [],
     "context_weight": {"crisis": 0.9, "normal": 1.2, "innovation": 1.2},
     "hybrid_eligible": True, "k_trait": 1.15, "description": "권한 위임·자율 부여로 구성원을 임파워먼트하는 리더",
     "strengths": ["자율성", "창의성", "주인의식"], "risks": ["과업 불확실성", "방향성 약화"],
     "anchor": ["M49-01"]},
    {"trait_id": "T107", "trait_type": "negative", "trait_kind": "risk", "trait_name": "Risk: Abusive Supervision",
     "required": ["N40-01"], "optional": ["N15-01", "N15-02", "N15-03"],
     "hard_forbidden": [], "soft_forbidden": [],
     "context_weight": {"crisis": 1.0, "normal": 1.1, "innovation": 1.0},
     "hybrid_eligible": False, "k_trait": 0.9, "description": "지속적 적대·모욕으로 구성원 존엄을 훼손하는 학대적 감독",
     "strengths": [], "risks": ["심리적 손상", "이직", "팀 붕괴"], "anchor": ["N40-01"]},
]


def load(p):
    with open(p, encoding="utf-8") as f:
        return json.load(f)


def dump(p, d):
    with open(p, "w", encoding="utf-8") as f:
        json.dump(d, f, ensure_ascii=False, indent=2)


# traits
td = load(TRAITS)
have = {t["trait_id"] for t in td["traits"]}
for t in td["traits"]:
    t["trait_kind"] = KIND.get(t["trait_id"], "risk" if t["trait_id"] in RISK else "style")
for nt in NEW_TRAITS:
    if nt["trait_id"] not in have:
        td["traits"].append(nt)
td["total_traits"] = len(td["traits"])
dump(TRAITS, td)

# micros
pos = load(POS)
pids = {m["label_id"] for m in pos["micro_labels"]}
for m in NEW_POS:
    if m["label_id"] not in pids:
        pos["micro_labels"].append(m)
pos["total_count"] = len(pos["micro_labels"])
dump(POS, pos)

neg = load(NEG)
nids = {m["label_id"] for m in neg["micro_labels"]}
for m in NEW_NEG:
    if m["label_id"] not in nids:
        neg["micro_labels"].append(m)
neg["total_count"] = len(neg["micro_labels"])
dump(NEG, neg)

print("v5 빌드 완료: trait_kind 부여, T15 Empowering·T107 Abusive 신설, M49-01/02·N40-01 micro 추가")
print(f"traits={len(td['traits'])} pos_micros={len(pos['micro_labels'])} neg_micros={len(neg['micro_labels'])}")
