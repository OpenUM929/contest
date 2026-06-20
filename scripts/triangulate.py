# -*- coding: utf-8 -*-
"""
M2 삼각검증 + M3 최신성 + M9 노몰로지컬:
 - 단일출처/구버전 구성개념에 독립 최신(2021+) 출처 추가
 - 각 구성개념에 expected outcomes(노몰로지컬 네트워크) 부착
확실한 DOI/URL만(허위 방지). 실행: python -X utf8 scripts/triangulate.py
"""
import json
import os

BASE = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
REG = os.path.join(BASE, "data/evidence/leadership_evidence_registry.json")

PLETZER = {"cite": "Pletzer, Breevaart & Bakker, Constructive & destructive leadership (JD-R) meta",
           "year": 2024, "type": "meta-analysis", "url": "https://journals.sagepub.com/doi/10.1177/20413866231197519",
           "doi": "10.1177/20413866231197519", "evidence_grade": "M", "peer_reviewed": True,
           "journal_tier": "Q1 (JLOS)", "claim_quote": "파괴적 리더십→소진·이직의도↑·웰빙·성과↓ (동기·건강손상 경로 메타)"}

NEW_SOURCES = {
    "toxic_destructive": [PLETZER],
    "abusive_supervision": [PLETZER],
    "laissez_faire": [PLETZER],
    "authentic": [{"cite": "Authentic leadership across culture: meta-analytic review (APJM)", "year": 2021,
                   "type": "meta-analysis", "url": "https://link.springer.com/article/10.1007/s10490-021-09762-0",
                   "doi": "10.1007/s10490-021-09762-0", "evidence_grade": "M", "peer_reviewed": True,
                   "journal_tier": "Q1 (Asia Pacific J. Management)", "n_studies": "214편, N=196,300",
                   "claim_quote": "214편/N=196,300; 만족·성과·OCB와 정적, 문화(권력거리·개인주의) 조절"}],
    "ethical": [{"cite": "Li et al., Ethical leadership meta-analysis (EJIM)", "year": 2024,
                 "type": "meta-analysis", "url": "https://www.inderscience.com/info/inarticle.php?artid=140922",
                 "doi": "", "evidence_grade": "M", "peer_reviewed": True, "journal_tier": "(EJIM 24:243-266)",
                 "claim_quote": "윤리적 리더십→발언·직무성과 정적(매개·조절 포함 메타)"}],
    "dark_triad": [{"cite": "Dark Triad in workplace leadership: systematic review (Behavioral Sciences)", "year": 2025,
                    "type": "SLR", "url": "https://www.mdpi.com/2076-328X/15/3/297", "doi": "10.3390/bs15030297",
                    "evidence_grade": "S", "peer_reviewed": True, "journal_tier": "(Behavioral Sciences)",
                    "claim_quote": "Dark Triad 리더: 단기 성공 가능하나 장기 조직건강 훼손"}],
    "participative": [{"cite": "Miao & Zhang, Participative leadership & voice (public servants)", "year": 2023,
                       "type": "primary", "url": "https://journals.sagepub.com/doi/abs/10.1177/00910260221147692",
                       "doi": "10.1177/00910260221147692", "evidence_grade": "E", "peer_reviewed": True,
                       "claim_quote": "참여적 리더십→발언행동(조직동일시 매개, 권력거리 조절)"}],
    "ambidextrous": [{"cite": "Kousina & Voudouris, Ambidextrous leadership & innovative behavior (PAR)", "year": 2023,
                      "type": "primary", "url": "https://onlinelibrary.wiley.com/doi/10.1111/puar.13650",
                      "doi": "10.1111/puar.13650", "evidence_grade": "E", "peer_reviewed": True,
                      "journal_tier": "Q1 (Public Administration Review)",
                      "claim_quote": "양손잡이 리더십→혁신행동(심리적 주인의식 매개)"}],
    "initiating_structure": [{"cite": "Ceri-Booms et al., Task- & person-focused leadership & team performance meta (HRMR)",
                              "year": 2017, "type": "meta-analysis",
                              "url": "https://www.sciencedirect.com/science/article/abs/pii/S105348221630064X",
                              "doi": "10.1016/j.hrmr.2016.09.010", "evidence_grade": "M", "peer_reviewed": True,
                              "journal_tier": "Q1 (HRM Review)", "claim_quote": "과업초점 리더행동→팀성과(메타, 조절변수 분석)"}],
}

OUTCOMES = {
    "transformational": "성과(+)·직무만족(+)·OCB(+)·조직몰입(+) — 메타 일관",
    "transactional_contingent_reward": "성과(+,중간)·만족(+) — 효과크기 작음",
    "servant": "상사신뢰(+,최대)·조직효과성(+)·OCB(+)",
    "empowering": "창의성(+)·OCB(+)·성과(+); 과도 자율→과업불확실성(−)",
    "participative": "발언(+)·만족(+)·창의성(+)",
    "authentic": "만족(+)·성과(+)·신뢰(+) — 단 변혁적과 중복",
    "ethical": "발언(+)·직무성과(+)·OCB(+)",
    "shared_distributed": "팀성과(+, ρ=.34)",
    "identity_social": "집단동일시(+)·추종(+)",
    "digital": "디지털 전환성과(+) — 측정 초기단계",
    "adaptive": "적응성과(+)·위기대응(+)",
    "toxic_destructive": "이직의도(+)·만족(−)·정서소진(+)·CWB(+)",
    "abusive_supervision": "이직의도(+)·만족(−)·CWB(+)·정서소진(+)",
    "laissez_faire": "만족(−)·역할모호(+)·성과(−)",
    "dark_triad": "단기성공(±)·장기 조직건강(−)·CWB(+)",
    "behavioral_integrity": "신뢰(+)·몰입(+)·OCB(+)·성과(+)",
    "initiating_structure": "팀/직무성과(+, ρ≈.29)",
    "ambidextrous": "혁신행동(+)·창의성(+)",
    "humble": "몰입(+)·팀성과(+)·혁신(+)",
    "inclusive": "소속감(+)·심리적안전(+)·참여(+)",
    "green_environmental": "직원 녹색행동/OCBE(+)",
}

with open(REG, encoding="utf-8") as f:
    reg = json.load(f)
added = 0
for c in reg["constructs"]:
    for ns in NEW_SOURCES.get(c["id"], []):
        if not any(s.get("doi") and s.get("doi") == ns.get("doi") for s in c["sources"]) \
           and not any(s.get("url") == ns["url"] for s in c["sources"]):
            c["sources"].append(ns)
            added += 1
    if c["id"] in OUTCOMES:
        c["expected_outcomes"] = OUTCOMES[c["id"]]
with open(REG, "w", encoding="utf-8") as f:
    json.dump(reg, f, ensure_ascii=False, indent=2)
print(f"삼각검증 출처 {added}건 추가 + 노몰로지컬 outcomes {len(OUTCOMES)}건 부착")
