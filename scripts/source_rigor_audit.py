# -*- coding: utf-8 -*-
"""
출처 강도 진단: 어디를 보강해야 정당성이 오르는지 정확히 지목.
플래그:
  R1 단일출처   : 출처 1개뿐(삼각검증 부재) → 독립 출처 보강 대상
  R2 최신성     : 최근 5년(>=2021) 출처 없음 → 최신 메타 보강 대상
  R3 강도필드   : 메타(M)인데 n_studies/effect_size 등 강도 메타데이터 없음
  R4 비동료심사 : 앵커 출처가 peer_reviewed=False(thesis/기타)
  R5 척도대응   : scale_item_map에 매핑 없음(차원 라벨 수준에 머묾)
실행: python -X utf8 scripts/source_rigor_audit.py
"""
import json
import os
from datetime import date

BASE = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))


def load(rel, default=None):
    p = os.path.join(BASE, rel)
    if not os.path.exists(p):
        return default
    with open(p, encoding="utf-8") as f:
        return json.load(f)


reg = load("data/evidence/leadership_evidence_registry.json")["constructs"]
scale_map = load("data/evidence/scale_item_map.json", {}) or {}
scale_keys = set(scale_map.get("constructs", {}).keys()) if scale_map else set()
YEAR_MIN = date.today().year - 5

flags = {f"R{i}": [] for i in range(1, 6)}
for c in reg:
    cid = c["id"]
    srcs = c.get("sources", [])
    years = [s.get("year", 0) for s in srcs]
    if len(srcs) < 2:
        flags["R1"].append(cid)
    if not any(y >= YEAR_MIN for y in years):
        flags["R2"].append(f"{cid}(최신 {max(years) if years else '-'})")
    for s in srcs:
        if s.get("evidence_grade") == "M" and not any(k in s for k in ("n_studies", "effect_size", "N")):
            flags["R3"].append(f"{cid}:{s.get('cite','?')[:24]}")
    if srcs and not srcs[0].get("peer_reviewed", False):
        flags["R4"].append(f"{cid}:{srcs[0].get('cite','?')[:24]}")
    if cid not in scale_keys:
        flags["R5"].append(cid)

print("=" * 60)
print(f"출처 강도 진단 (구성개념 {len(reg)}개, 최신성 기준 ≥{YEAR_MIN})")
print("=" * 60)
labels = {"R1": "단일출처(삼각검증 필요)", "R2": "최신성 부족(≥2021 없음)",
          "R3": "강도 메타데이터 없음(메타인데 k/N/효과 미기록)",
          "R4": "비동료심사 앵커(thesis 등)", "R5": "척도-문항 대응 없음"}
for code in ("R1", "R2", "R3", "R4", "R5"):
    items = flags[code]
    print(f"\n[{code}] {labels[code]} — {len(items)}건")
    for it in items:
        print(f"    - {it}")

total = sum(len(v) for v in flags.values())
print("\n" + "-" * 60)
print(f"총 보강 지점 {total}건. 우선순위: R5(척도대응)·R1(삼각검증) > R3·R2 > R4.")
print("=" * 60)
