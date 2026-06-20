# -*- coding: utf-8 -*-
"""
리더십 구성개념 '추세' 리포트.
data/evidence/leadership_evidence_registry.json 을 읽어 시대별 위상 변화와
taxonomy 조치가 필요한 신호(중복/누락/논쟁/재검토 기한)를 출력한다.

핵심 아이디어: validity_status(견고/구별성) 와 attention_trend(관심 추세)를 분리해
'관심은 오르는데 타당도는 논쟁'(authentic 등) 같은 *괴리 신호*를 잡는다.
이게 "시대에 따라 갱신해야 할" 1순위 항목.

실행: python -X utf8 scripts/evidence_trends.py
"""
import json
import os
from datetime import date

BASE = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
REG = os.path.join(BASE, "data/evidence/leadership_evidence_registry.json")

with open(REG, encoding="utf-8") as f:
    reg = json.load(f)

cons = reg["constructs"]
ARROW = {"rising": "↑", "stable": "→", "declining": "↓"}
TODAY = date.today().isoformat()

print("=" * 72)
print(f"리더십 구성개념 추세 리포트  (last_full_review={reg['last_full_review']}, "
      f"next_due={reg['next_review_due']})")
print("=" * 72)

# ---- 전체 스냅샷 ----
print(f"\n{'구성개념':<22}{'극성':<5}{'위상':<12}{'관심':<5}{'증분/효과':<22}{'조치':<11}{'trait'}")
print("-" * 100)
for c in sorted(cons, key=lambda x: (x["polarity"], x["validity_status"])):
    traits = ",".join(c["mapped_traits"]) if c["mapped_traits"] else "-"
    print(f"{c['name_ko']:<22}{c['polarity'][:3]:<5}{c['validity_status']:<12}"
          f"{ARROW.get(c['attention_trend'],'?'):<5}{(c.get('incremental_validity') or '-')[:20]:<22}"
          f"{c['implication']:<11}{traits}")

# ---- 신호 1: 괴리(관심↑ + 위상 논쟁/중복) = 별도 trait 정당성 약화 ----
print("\n[신호 1] 관심 상승 vs 타당도 논쟁/중복 — 별도 trait 정당성 약함(흡수 검토)")
gap = [c for c in cons if c["attention_trend"] == "rising"
       and c["validity_status"] in ("contested", "redundant")]
for c in gap or []:
    print(f"  ⚡ {c['name_ko']} (traits={c['mapped_traits'] or '-'}): {c['trend_note']}")
if not gap:
    print("  (없음)")

# ---- 신호 2: 신설/보강 후보(구별성 있는데 미매핑 or 파편) ----
print("\n[신호 2] 신설·보강 후보 — 경험적으로 구별되나 미매핑/파편(implication=add)")
for c in [c for c in cons if c["implication"] == "add"]:
    print(f"  ＋ {c['name_ko']} (현재 traits={c['mapped_traits'] or '없음'}): {c['trend_note']}")

# ---- 신호 3: 통합/폐기 후보 ----
print("\n[신호 3] 통합·폐기 후보 (implication=merge/deprecate)")
for c in [c for c in cons if c["implication"] in ("merge", "deprecate")]:
    print(f"  ↘ {c['name_ko']} → {c['implication']}: {c['trend_note']}")

# ---- 신호 4: 범위 밖(분석수준 경계) ----
oos = [c for c in cons if c["implication"] == "out_of_scope"]
if oos:
    print("\n[신호 4] 범위 밖(분석수준 경계 결정 필요)")
    for c in oos:
        print(f"  ◌ {c['name_ko']}: {c['trend_note']}")

# ---- 재검토 기한 ----
print("\n[재검토] " + ("⚠️ 기한 지남 — 문헌 재조사 필요!"
      if TODAY >= reg["next_review_due"] else
      f"다음 재검토 예정일 {reg['next_review_due']} (cadence {reg['review_cadence_months']}개월)"))
print("=" * 72)
