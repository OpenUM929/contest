# -*- coding: utf-8 -*-
"""
Taxonomy 회귀 게이트 — 라벨/trait이 늘어날 때마다 돌려서 구조 불변식을 강제한다.
신규 micro/trait 추가 시 이게 통과 못 하면 머지 금지.

불변식(src/taxonomy.py 의 check_invariants):
  I1 anchor   : 모든 trait은 required 안의 살아있는 앵커 >= 1 (공유 hub 단독 점화 금지)
  I2 orphan   : 학습데이터 있는 라벨은 어떤 trait에든 연결 (orphan=0)
  I3 deprecated: superseded_by 는 살아있는 라벨을 가리킴(체인 해소)
  I4 ref      : trait이 참조하는 라벨 실존 + deprecated 직접참조 금지
  I5 dup      : label_id 중복 정의 금지
  I6 dupname  : 살아있는 라벨끼리 동일 label_name 금지(과세분/복제 탐지)

종료코드: 위반 있으면 1, 통과 0. (CI/pre-commit 게이트로 사용)
"""
import os
import sys

sys.path.insert(0, os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "src"))
from taxonomy import Taxonomy  # noqa: E402

tax = Taxonomy.load()

print("=" * 60)
print("Taxonomy 불변식 검증")
print("=" * 60)
print(f"micros={len(tax.micros)}  traits={len(tax.traits)}  "
      f"deprecated={len(tax.deprecated_ids())}  orphans={len(tax.orphans())}")

issues = tax.check_invariants()

# 분류별 집계
buckets = {}
for s in issues:
    tag = s.split("]")[0].lstrip("[").split()[0]
    buckets.setdefault(tag, []).append(s)

print("\n[불변식별 결과]")
for code in ("I1", "I2", "I3", "I4", "I5", "I6"):
    items = buckets.get(code, [])
    mark = "OK " if not items else "FAIL"
    print(f"  {code}: [{mark}] {len(items)}건")

if issues:
    print(f"\n[위반 상세] 총 {len(issues)}건")
    for s in issues:
        print(f"  {s}")
    print("\n" + "=" * 60)
    print(f"[FAIL] 불변식 위반 {len(issues)}건 — 라벨/trait 정의 수정 필요")
    print("=" * 60)
    sys.exit(1)

print("\n" + "=" * 60)
print("[OK] 모든 불변식 통과 — 확장 안전")
print("=" * 60)
sys.exit(0)
