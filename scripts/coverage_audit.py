# -*- coding: utf-8 -*-
"""
Phase2 커버리지 감사: '사후매핑→이론선행'을 강제하기 위한 진단.
causal_rationale의 trait_links를 역인덱싱해 각 trait이 *학술 구성개념의 정의 차원*을
부모로 갖는지 확인한다. 부모 없는 trait = 근거가 사후에도 안 붙은 구성타당도 결함.

또 레지스트리의 implication=add(미매핑 구성개념)로 '누락 구성개념'을 보고.
실행: python -X utf8 scripts/coverage_audit.py
"""
import json
import os
import sys
from collections import defaultdict

BASE = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, os.path.join(BASE, "src"))
from taxonomy import Taxonomy  # noqa: E402


def load(rel):
    with open(os.path.join(BASE, rel), encoding="utf-8") as f:
        return json.load(f)


tax = Taxonomy.load()
causal = load("data/evidence/causal_rationale.json")["constructs"]
reg = load("data/evidence/leadership_evidence_registry.json")["constructs"]

# trait -> [(construct, dimension)]
parent = defaultdict(list)
for cid, c in causal.items():
    for tl in c.get("trait_links", []):
        parent[tl["trait"]].append((cid, tl.get("instantiates", "")))

all_traits = list(tax.traits.keys())

# trait_kind 인식: style/risk만 학술 '구성개념 부모' 필요. capability/context는 by-design.
def kind(t):
    return tax.traits[t].get("trait_kind", "style")

need_parent = [t for t in all_traits if kind(t) in ("style", "risk")]
by_design = [t for t in all_traits if kind(t) in ("capability", "context")]
with_parent = [t for t in need_parent if parent.get(t)]
without = [t for t in need_parent if not parent.get(t)]

print("=" * 64)
print("Phase2 커버리지 감사 — trait의 학술 구성개념 부모(dimensional parent)")
print("=" * 64)
print(f"trait {len(all_traits)}개 (부모필요 style/risk {len(need_parent)} · by-design capability/context {len(by_design)})")
print(f"부모필요 중 보유 {len(with_parent)} · 없음 {len(without)} "
      f"({len(with_parent)/len(need_parent):.0%})")
if by_design:
    print("  [by-design 제외] " + ", ".join(f"{t}({kind(t)})" for t in by_design))

print("\n[부모 보유]")
for t in all_traits:
    if parent.get(t):
        ps = "; ".join(f"{cid}:{dim}" for cid, dim in parent[t])
        print(f"  {t} {tax.traits[t]['trait_name']:<30} ← {ps}")

print("\n[부모 없음 = 구성타당도 백로그(사후매핑도 안 됨)]")
for t in without:
    print(f"  ⚠ {t} {tax.traits[t]['trait_name']}  → 차원 부모 지정 또는 역량/맥락 재분류/통합 필요")

# 누락 구성개념(implication=add, 미매핑)
print("\n[누락 구성개념 = 신설 후보(implication=add, 현재 trait 미연계)]")
for c in reg:
    if c["implication"] == "add" and not c["mapped_traits"]:
        print(f"  ＋ {c['name_ko']} ({c['id']})")

print("\n" + "-" * 64)
cov = len(with_parent) / len(need_parent)
print(f"부모 커버리지(style/risk) {cov:.0%} (목표 ≥80%). 부모없음 {len(without)}건이 결정 대상.")
print("=" * 64)
