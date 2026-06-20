# -*- coding: utf-8 -*-
"""
Phase1: 플래그된 2차 경로(blog/researchgate)를 1차 출처로 교체 + 핵심 정량주장에 claim_quote 부착.
construct-aware(같은 url이라도 construct별로 올바른 1차 출처로 치환).
실행: python -X utf8 scripts/fix_sources.py
"""
import json
import os

BASE = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
REG = os.path.join(BASE, "data/evidence/leadership_evidence_registry.json")
CAU = os.path.join(BASE, "data/evidence/causal_rationale.json")

ANTONAKIS = {"cite": "Antonakis, Avolio & Sivasubramaniam, Context and leadership: nine-factor full-range (MLQ)",
             "year": 2003, "type": "primary",
             "url": "https://www.sciencedirect.com/science/article/abs/pii/S1048984303000304",
             "doi": "10.1016/S1048-9843(03)00030-4", "evidence_grade": "E", "peer_reviewed": True,
             "claim_quote": "9요인 구조(변혁 5·거래 3·laissez-faire 1)를 MLQ로 확인 (Leadership Quarterly 14:261-295)"}
PAULHUS = {"cite": "Paulhus & Williams, The Dark Triad of Personality",
           "year": 2002, "type": "primary",
           "url": "https://doi.org/10.1016/S0092-6566(02)00505-6",
           "doi": "10.1016/S0092-6566(02)00505-6", "evidence_grade": "E", "peer_reviewed": True,
           "claim_quote": "Narcissism·Machiavellianism·Psychopathy 3요인 정의 (J. Research in Personality 36:556-563)"}
SCHMIDT = {"cite": "Schmidt, Development and Validation of the Toxic Leadership Scale (PhD thesis, Univ. of Maryland; dir. Hanges)",
           "year": 2008, "type": "scale",
           "url": "https://www.proquest.com/openview/2d4bf487b9961c7a5eedb5af1aefe456/1",
           "doi": "", "evidence_grade": "E", "peer_reviewed": False,
           "claim_quote": "5차원: abusive supervision(α=.93)·authoritarian(.89)·narcissism(.88)·self-promotion(.91)·unpredictability(.92)"}

# construct id -> (감지 substring, 교체 레코드)
REPLACE = {
    "transformational": ("leadershipahoy.com", ANTONAKIS),
    "laissez_faire": ("leadershipahoy.com", ANTONAKIS),
    "dark_triad": ("researchgate.net", PAULHUS),
    "toxic_destructive": ("researchgate.net", SCHMIDT),
    "abusive_supervision": ("researchgate.net", SCHMIDT),
}

# construct id -> claim_quote (정량 주장 출처에 부착; cite substring으로 매칭)
CLAIM_QUOTES = {
    "servant": ("Hoch", "변혁적 대비 증분: 조직성과 +12%, 상사신뢰 +19% (Hoch et al. 2018 메타)"),
    "transactional_contingent_reward": ("박동필", "588편/839 효과크기; 조직효과성 서번트 최대·거래적 최소"),
    "shared_distributed": ("Wang", "공유리더십–팀효과 ρ=.34 (메타)"),
    "empowering": ("Lee", "임파워링→성과·OCB·창의성 증분기여 (105표본 메타)"),
    "humble": ("Chiu", "212편 메타: 몰입·팀성과·혁신에 정효과"),
    "identity_social": ("Steffens", "리더 집단프로토타입성–추종 정효과 (메타)"),
    "authentic": ("Hoch", "변혁적과 상관 높아 증분 5~11%에 그침(중복) (Hoch et al. 2018)"),
    "ethical": ("Hoch", "변혁적과 상관 높아 증분 5~11%에 그침(중복) (Hoch et al. 2018)"),
}


def patch_source_list(cid, sources):
    sub_rec = REPLACE.get(cid)
    for i, s in enumerate(sources):
        if sub_rec and sub_rec[0] in s.get("url", ""):
            sources[i] = dict(sub_rec[1])
    # claim_quote 부착
    cq = CLAIM_QUOTES.get(cid)
    if cq:
        for s in sources:
            if cq[0] in s.get("cite", "") and "claim_quote" not in s:
                s["claim_quote"] = cq[1]


# 레지스트리
with open(REG, encoding="utf-8") as f:
    reg = json.load(f)
for c in reg["constructs"]:
    patch_source_list(c["id"], c.get("sources", []))
with open(REG, "w", encoding="utf-8") as f:
    json.dump(reg, f, ensure_ascii=False, indent=2)

# causal dimensions_source
with open(CAU, encoding="utf-8") as f:
    cau = json.load(f)
for cid, c in cau["constructs"].items():
    ds = c.get("dimensions_source")
    if ds:
        sub_rec = REPLACE.get(cid)
        if sub_rec and sub_rec[0] in ds.get("url", ""):
            c["dimensions_source"] = dict(sub_rec[1])
with open(CAU, "w", encoding="utf-8") as f:
    json.dump(cau, f, ensure_ascii=False, indent=2)

print("교체/인용구 부착 완료. 재검증은 validate_evidence.py로.")
