# -*- coding: utf-8 -*-
"""
M1 강도 메타데이터 부착: 확실히 아는 값만(효과크기·표본수·저널등급).
모르는 값은 채우지 않음(허위 방지). 출처에 n_studies/effect_size/journal_tier 추가.
실행: python -X utf8 scripts/rigor_uplift.py
"""
import json
import os

BASE = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
REG = os.path.join(BASE, "data/evidence/leadership_evidence_registry.json")

# construct -> [(cite_substr, {fields})]
PATCH = {
    "transactional_contingent_reward": [("박동필", {"n_studies": "588편/839 효과크기", "journal_tier": "KCI"})],
    "servant": [("Hoch", {"effect_size": "조직성과 +12%·신뢰 +19% 증분", "journal_tier": "Q1 (J. of Management)"}),
                ("박동필", {"n_studies": "588편/839 효과크기", "journal_tier": "KCI"})],
    "authentic": [("Hoch", {"effect_size": "증분 5~11%(중복)", "journal_tier": "Q1 (J. of Management)"})],
    "ethical": [("Hoch", {"effect_size": "증분 5~11%(중복)", "journal_tier": "Q1 (J. of Management)"})],
    "shared_distributed": [("Wang", {"effect_size": "ρ=.34(팀효과)", "journal_tier": "Q1 (JAP)"})],
    "empowering": [("Lee", {"n_studies": "105 samples", "journal_tier": "Q1 (JOB)"}),
                   ("Kim", {"journal_tier": "Q1 (JLOS)"})],
    "humble": [("Chiu", {"n_studies": "212 studies", "journal_tier": "Q1 (Leadership Quarterly)"}),
               ("Wu", {"journal_tier": "Q1 (JLOS)"})],
    "identity_social": [("Steffens", {"journal_tier": "Q1 (Group Processes & IR)"})],
    "initiating_structure": [("Judge", {"n_studies": "163/159 correlations",
                                         "effect_size": "IS ρ=.29, Consideration ρ=.48", "journal_tier": "Q1 (JAP)"})],
}

with open(REG, encoding="utf-8") as f:
    reg = json.load(f)
n = 0
for c in reg["constructs"]:
    for sub, fields in PATCH.get(c["id"], []):
        for s in c.get("sources", []):
            if sub in s.get("cite", ""):
                s.update(fields)
                n += 1
with open(REG, "w", encoding="utf-8") as f:
    json.dump(reg, f, ensure_ascii=False, indent=2)
print(f"강도 메타데이터 부착: {n}건")
