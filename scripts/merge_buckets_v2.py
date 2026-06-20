# -*- coding: utf-8 -*-
"""
버킷 v2 = 구조신호(휴리스틱) + 경험적 F1 결합 보정
=================================================
발견: 구조신호 기반 A/B 버킷이 경험적 분류 난이도를 예측하지 못함(오히려 역전).
- 단, 부정라벨의 '높은 F1'은 데이터가 단문·고립 샘플이라 생긴 artifact
  (실제 hard 케이스: 맥락 뒤집힘/역접/문장간 의도 — 데이터에 없음).
보정 규칙:
  - 구조신호 B(추론위험 高) → 무조건 B 유지 (clean F1 높아도 production hard 케이스 못 봄)
  - 그 외(저위험): 경험적 F1로 재배치  F1≥.70→A / .50~.70→C / <.50→B*(혼동·계층화 필요)
"""
import re, os
BASE = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
md = open(os.path.join(BASE, "docs/baseline_classifier_report.md"), encoding="utf-8").read()

rows = []
for m in re.finditer(r"\|\s*([MN]\d+-\d+)\s*\|\s*([ABC?])\s*\|\s*(pos|neg)\s*\|\s*([\d.]+)\s*\|\s*(Y?)\s*\|", md):
    lid, b, typ, f1, orph = m.group(1), m.group(2), m.group(3), float(m.group(4)), m.group(5)
    rows.append((lid, b, typ, f1, orph == "Y"))

def v2(b, f1):
    if b == "B": return "B"            # 구조적 추론 위험 → 유지
    if f1 >= 0.70: return "A"
    if f1 >= 0.50: return "C"
    return "B*"                         # 저위험인데 혼동 큼 → 병합/계층화 대상

from collections import Counter
cnt = Counter(); moved_down = []
for lid, b, typ, f1, orph in rows:
    nb = v2(b, f1)
    cnt[nb] += 1
    if b == "A" and nb in ("C", "B*"):
        moved_down.append((lid, f1, orph))

print("=== 버킷 v2 (구조신호 + 경험적 F1) ===")
for k in ("A", "C", "B", "B*"):
    print(f"  {k:<3}: {cnt.get(k,0)}개")
print(f"\n분류기 단독 신뢰(A): {cnt.get('A',0)}개")
print(f"규칙/계층 보정(C+B*): {cnt.get('C',0)+cnt.get('B*',0)}개")
print(f"추론 전담(B): {cnt.get('B',0)}개")

print("\n=== A버킷 개선: 구버전 A → 강등된 라벨 (orphan 거품 제거) ===")
for lid, f1, orph in sorted(moved_down, key=lambda x: x[1]):
    print(f"  {lid}  F1={f1:.2f}{'  [orphan]' if orph else ''} → 강등")

# 진짜 A (구조 저위험 + 고F1) 목록
true_a = [(lid, f1) for lid, b, typ, f1, orph in rows if v2(b, f1) == "A"]
print(f"\n=== v2 A버킷(진짜 분류기 신뢰) {len(true_a)}개 ===")
for lid, f1 in sorted(true_a, key=lambda x: -x[1])[:20]:
    print(f"  {lid}  F1={f1:.2f}")

# B* (병합/계층화 후보) 목록
bstar = [(lid, f1) for lid, b, typ, f1, orph in rows if v2(b, f1) == "B*"]
print(f"\n=== B* (저위험인데 혼동 → 라벨 병합/계층화 후보) {len(bstar)}개 ===")
for lid, f1 in sorted(bstar, key=lambda x: x[1]):
    print(f"  {lid}  F1={f1:.2f}")
