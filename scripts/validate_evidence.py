# -*- coding: utf-8 -*-
"""
Phase1 게이트: 출처 품질 불변식.
  E1: 모든 source에 evidence_grade(M/S/E/R/B) 존재
  E2: 2차 경로(blog/researchgate/academia/studocu 등) 0건  ← 핵심
  E3: 정량 주장(incremental_validity가 수치 포함) 구성개념은 claim_quote 보유 출처 ≥1
  E4: peer_reviewed 출처 비율 ≥ 0.7 (B/thesis 제외 분모)
종료코드: 위반 시 1.
실행: python -X utf8 scripts/validate_evidence.py
"""
import json
import os
import re

BASE = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
REG = os.path.join(BASE, "data/evidence/leadership_evidence_registry.json")

SECONDARY = ("leadershipahoy.com", "researchgate.net", "academia.edu",
             "studocu.com", "scribd.com", "wikipedia.org", "wordpress.com",
             "statisticssolutions.com", "linkedin.com")
GRADES = {"M", "S", "E", "R", "B"}
NUM = re.compile(r"\d")

with open(REG, encoding="utf-8") as f:
    reg = json.load(f)

issues = []
all_src = []
for c in reg["constructs"]:
    srcs = c.get("sources", [])
    all_src += srcs
    for s in srcs:
        tag = f"{c['id']}:{s.get('cite','?')[:30]}"
        if s.get("evidence_grade") not in GRADES:
            issues.append(f"[E1 grade] {tag} evidence_grade 누락/오류")
        if any(d in s.get("url", "") for d in SECONDARY):
            issues.append(f"[E2 2차경로] {tag} → {s.get('url')}")
    # E3: 정량 주장인데 claim_quote 없는 경우
    iv = c.get("incremental_validity", "") or ""
    if NUM.search(iv) and not any(s.get("claim_quote") for s in srcs):
        issues.append(f"[E3 quote] {c['id']} 정량주장('{iv[:24]}')인데 claim_quote 없음")

# E4: peer_reviewed 비율 (grade B/thesis 제외)
elig = [s for s in all_src if s.get("evidence_grade") != "B"]
pr = [s for s in elig if s.get("peer_reviewed")]
ratio = len(pr) / len(elig) if elig else 1.0

print("=" * 56)
print("출처 품질 검증 (Phase1)")
print("=" * 56)
print(f"출처 {len(all_src)}건 · peer_reviewed 비율(B 제외) {ratio:.0%}")
for code in ("E1", "E2", "E3"):
    n = len([i for i in issues if i.startswith(f'[{code}')])
    print(f"  {code}: {'OK ' if n == 0 else 'FAIL'} {n}건")
print(f"  E4: {'OK ' if ratio >= 0.7 else 'FAIL'} (기준 70%)")

if ratio < 0.7:
    issues.append(f"[E4 peer] peer_reviewed 비율 {ratio:.0%} < 70%")

if issues:
    print("\n[위반]")
    for i in issues:
        print(" ", i)
    print("\n[FAIL] 출처 품질 미충족")
    raise SystemExit(1)
print("\n[OK] 출처 품질 통과")
