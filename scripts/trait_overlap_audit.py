# -*- coding: utf-8 -*-
"""
Trait 과호출(over-firing) 구조 감사
===================================
"왜 한 입력에 여러 trait이 켜지나?" — 모델이 아니라 '구조'를 본다.
micro 라벨이 여러 trait의 구성요소로 '공유'될수록, 그 micro 하나가
여러 trait을 동시에 밀어올린다. 순수 구조 분석(분류기·데이터 불필요).

산출:
  (1) Hub micro      : 여러 trait에 걸친 라벨 (fan-out) → 과호출의 원천
  (2) required 공유  : 여러 trait의 '필수'로 동시에 박힌 라벨 → 강제 co-fire
  (3) trait 쌍 중첩  : 시그니처(required+optional) Jaccard → 사실상 중복 trait
  (4) 앵커 없는 trait: 자기만의 고유(unique) 필수 라벨이 없음 → 정밀 호출 불가

설계 원칙(향후 추가 대비):
  - 정밀도는 '공유 hub'가 아니라 trait마다의 '앵커(고유 라벨)'에서 나온다.
  - micro/trait 추가 시: 신규 trait은 앵커 1개 이상 선언, 신규 micro는
    discriminative(고유) / supporting(공유) 역할을 명시.
"""
import json, os, re
from collections import defaultdict
from itertools import combinations

BASE = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
def P(*a): return os.path.join(BASE, *a)
def load(p):
    with open(P(p), encoding="utf-8") as f:
        return json.load(f)

traits   = load("data/traits/trait_definitions.json")["traits"]
pos_defs = load("dataset/ori/positive_micro_labels_enhanced.json")["micro_labels"]
neg_defs = load("dataset/ori/negative_micro_labels_enhanced.json")["micro_labels"]
name = {d["label_id"]: d.get("label_name", "") for d in pos_defs + neg_defs}
tname = {t["trait_id"]: t["trait_name"] for t in traits}

# ---- 시그니처 구성 ----
sig, req = {}, {}
for t in traits:
    tid = t["trait_id"]
    req[tid] = set(t.get("required", []))
    sig[tid] = set(t.get("required", [])) | set(t.get("optional", []))

fan, reqfan = defaultdict(set), defaultdict(set)
for tid in sig:
    for m in sig[tid]:  fan[m].add(tid)
    for m in req[tid]:  reqfan[m].add(tid)

# =====================================================================
out = []; W = out.append
W("# Trait 과호출(over-firing) 구조 감사")
W("")
W("> 순수 구조 분석. '한 입력에 여러 trait이 켜지는' 원인 = micro 신호 공유.")
W("> 정밀 호출의 열쇠: trait마다 **고유 앵커(unique required)** 확보 + 공유 hub 가중치 하향.")
W("")

# (1) Hub micro
W("## 1. Hub micro — 여러 trait에 걸친 라벨 (과호출의 원천)")
W("")
W("fan-out = 이 micro가 구성요소로 들어간 trait 수. 높을수록 이 라벨 하나가 여러 trait을 켠다.")
W("")
W("| micro | 이름 | fan-out | 소속 trait |")
W("|-------|------|---------|-----------|")
hubs = sorted(fan.items(), key=lambda x: -len(x[1]))
for m, ts in hubs:
    if len(ts) >= 3:
        W(f"| {m} | {name.get(m,'?')} | **{len(ts)}** | {', '.join(sorted(ts))} |")
W("")

# (2) required 공유 = 강제 co-fire
W("## 2. required 공유 — 여러 trait의 '필수'에 동시에 박힌 라벨")
W("")
W("이 라벨이 탐지되면 **여러 trait이 동시에 필수조건을 충족**받는다 → 가장 직접적인 과호출 원인.")
W("")
W("| micro | 이름 | 필수인 trait |")
W("|-------|------|-------------|")
forced = sorted([(m, ts) for m, ts in reqfan.items() if len(ts) >= 2], key=lambda x: -len(x[1]))
for m, ts in forced:
    W(f"| {m} | {name.get(m,'?')} | {', '.join(f'{t}({tname[t]})' for t in sorted(ts))} |")
if not forced:
    W("| — | (없음) | |")
W("")

# (3) trait 쌍 중첩
W("## 3. Trait 쌍 시그니처 중첩 (Jaccard) — 사실상 중복")
W("")
W("두 trait의 (required+optional) 집합이 얼마나 겹치나. 높으면 같은 증거에 둘 다 켜진다.")
W("")
W("| trait A | trait B | 공유 | Jaccard |")
W("|---------|---------|------|---------|")
pairs = []
for a, b in combinations(sorted(sig), 2):
    inter = sig[a] & sig[b]
    if not inter:
        continue
    union = sig[a] | sig[b]
    pairs.append((len(inter) / len(union), len(inter), a, b, inter))
pairs.sort(key=lambda x: -x[0])
for j, ni, a, b, inter in pairs[:15]:
    W(f"| {a} {tname[a]} | {b} {tname[b]} | {ni}개 | **{j:.2f}** |")
W("")

# (4) 앵커 없는 trait
W("## 4. 앵커 없는 trait — 고유 필수 라벨이 없어 정밀 호출 불가")
W("")
W("앵커 = 그 trait에만 있는(fan-out=1) required 라벨. 앵커가 없으면 이 trait은")
W("**공유 라벨만으로 호출**되어 다른 trait과 항상 같이 켜진다.")
W("")
W("| trait | 고유필수(앵커) | 고유선택 | 시그니처 | 진단 |")
W("|-------|--------------|---------|---------|------|")
for t in traits:
    tid = t["trait_id"]
    anchors = [m for m in req[tid] if len(fan[m]) == 1]
    uniq_opt = [m for m in (sig[tid] - req[tid]) if len(fan[m]) == 1]
    diag = "✅ 앵커있음" if anchors else ("⚠️ 앵커없음" if sig[tid] else "—")
    W(f"| {tid} {tname[tid]} | {len(anchors)} ({', '.join(anchors) if anchors else '없음'}) | {len(uniq_opt)} | {len(sig[tid])} | {diag} |")
W("")

# 콘솔 요약 + 설계 원칙
W("## 5. 향후 추가를 위한 설계 원칙")
W("")
W("1. **앵커 우선**: 신규 trait은 fan-out=1 짜리 고유 필수 라벨(앵커)을 최소 1개 선언.")
W("2. **역할 명시**: 신규 micro에 `role: discriminative|supporting` 부여 — 공유 hub는 supporting으로 가중치↓.")
W("3. **추가만, 재번호 금지**: 라벨/ trait ID는 append-only. 폐기는 `deprecated:true`로 표시(삭제 X) → 과거 데이터 호환.")
W("4. **호출 점수**: trait 점수 = Σ(앵커 가중치 高 + supporting 가중치 低). hub만으로는 임계 못 넘게.")

open(P("docs/trait_overlap_audit.md"), "w", encoding="utf-8").write("\n".join(out))

no_anchor = [t["trait_id"] for t in traits
             if sig[t["trait_id"]] and not [m for m in req[t["trait_id"]] if len(fan[m]) == 1]]
print(f"Hub micro(fan-out≥3): {sum(1 for m,ts in fan.items() if len(ts)>=3)}개")
print(f"required 공유(강제 co-fire): {len(forced)}개 → {[m for m,_ in forced]}")
print(f"고중첩 trait쌍(Jaccard≥0.3): {sum(1 for p in pairs if p[0]>=0.3)}개")
print(f"앵커 없는 trait: {len(no_anchor)}개 → {no_anchor}")
print("\n리포트: docs/trait_overlap_audit.md")
