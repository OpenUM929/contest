# -*- coding: utf-8 -*-
"""
인과 논증 강화 (C3 메커니즘 + C6 증거유형):
각 구성개념에 causal_evidence{mechanism(매개), evidence_type(종단/실험/횡단/이론)} 부착.
메타가 보고한 매개·연구설계에 근거(허위 방지: 근거 있는 것만).
실행: python -X utf8 scripts/causal_uplift.py
"""
import json
import os

BASE = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
REG = os.path.join(BASE, "data/evidence/leadership_evidence_registry.json")

# construct -> {mechanism, evidence_type}
CE = {
    "transformational": {"mechanism": "동기부여·조직동일시 매개", "evidence_type": "횡단 메타(일부 종단)"},
    "transactional_contingent_reward": {"mechanism": "기대명확화·공정성 지각 매개", "evidence_type": "횡단 메타"},
    "servant": {"mechanism": "상사신뢰 매개", "evidence_type": "횡단 메타"},
    "empowering": {"mechanism": "심리적 임파워먼트·신뢰 매개", "evidence_type": "횡단 메타(일부 실험)"},
    "participative": {"mechanism": "조직동일시 매개", "evidence_type": "횡단(권력거리 조절)"},
    "authentic": {"mechanism": "LMX·직무만족 매개", "evidence_type": "횡단 메타(문화 조절)"},
    "ethical": {"mechanism": "내재적 동기 매개", "evidence_type": "횡단 메타"},
    "shared_distributed": {"mechanism": "팀 신뢰·조정 매개", "evidence_type": "횡단 메타(팀수준)"},
    "toxic_destructive": {"mechanism": "조직부정의·정서소진 매개", "evidence_type": "종단 메타(Pletzer 2024)"},
    "abusive_supervision": {"mechanism": "지각된 부정의·정서소진 매개", "evidence_type": "종단/횡단 메타"},
    "laissez_faire": {"mechanism": "역할모호·자원고갈 매개", "evidence_type": "종단 메타(Pletzer 2024)"},
    "dark_triad": {"mechanism": "사회적교환 훼손", "evidence_type": "횡단 SLR/메타"},
    "behavioral_integrity": {"mechanism": "신뢰 매개", "evidence_type": "횡단 메타(Simons)"},
    "initiating_structure": {"mechanism": "역할명확성 매개", "evidence_type": "횡단 메타"},
    "ambidextrous": {"mechanism": "심리적 주인의식 매개", "evidence_type": "횡단(매개 검증)"},
    "humble": {"mechanism": "관계·자기효능 매개", "evidence_type": "횡단 메타"},
    "inclusive": {"mechanism": "심리적 안전·소속감 매개", "evidence_type": "횡단"},
    "adaptive": {"mechanism": "—(측정 미정)", "evidence_type": "횡단/SLR"},
    "digital": {"mechanism": "—(SLR 단계)", "evidence_type": "SLR(인과 미확립)"},
    "identity_social": {"mechanism": "집단동일시 매개", "evidence_type": "횡단 메타(프로토타입성)"},
    "green_environmental": {"mechanism": "녹색풍토·녹색몰입 매개", "evidence_type": "횡단"},
}

with open(REG, encoding="utf-8") as f:
    reg = json.load(f)
n = 0
for c in reg["constructs"]:
    if c["id"] in CE:
        c["causal_evidence"] = CE[c["id"]]
        n += 1
with open(REG, "w", encoding="utf-8") as f:
    json.dump(reg, f, ensure_ascii=False, indent=2)
print(f"causal_evidence(메커니즘+증거유형) 부착: {n}건")
