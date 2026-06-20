# -*- coding: utf-8 -*-
"""
Taxonomy 감사 (라벨 정리 + trait 군집 재검토)
=============================================
"더 좋은 모델"이 아니라 "라벨 체계가 분리 가능한가"를 먼저 본다.
현재 데이터(고립·단문 샘플)로 TF-IDF 분류기를 학습 → 혼동행렬을 뽑아
다음 셋을 분리한다.

  (A) Orphan        : 학습데이터는 있는데 어떤 trait의 required/optional에도 없음
  (B) 과세분(macro) : 같은 macro 안 micro들이 서로 뭉개짐 → 병합/2단 분류 후보
  (C) trait 경계 혼동: 서로 다른 trait 소속인데 체계적으로 혼동 → 배치 오류 신호

주의: 현재 데이터는 '표면(어휘) 분리성'만 보여준다. 산출물은 '병합/재배치 후보'
이며 자동 결정이 아니다. 최종 판단은 도메인(사람) 몫.
"""
import json, os, re, random
from collections import Counter, defaultdict
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.linear_model import LogisticRegression
from sklearn.metrics import f1_score

random.seed(42)
BASE = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
def P(*a): return os.path.join(BASE, *a)
def load(p):
    with open(P(p), encoding="utf-8") as f:
        return json.load(f)

train_raw = load("dataset/ori/training_data_all_labels.json")
pos_defs  = load("dataset/ori/positive_micro_labels_enhanced.json")["micro_labels"]
neg_defs  = load("dataset/ori/negative_micro_labels_enhanced.json")["micro_labels"]
traits    = load("data/traits/trait_definitions.json")["traits"]

# ---- 라벨 메타 (이름/정의/macro) ----
meta = {}
for d in pos_defs + neg_defs:
    meta[d["label_id"]] = {
        "name": d.get("label_name", ""),
        "macro": d.get("macro", re.match(r"([MN]\d+)-", d["label_id"]).group(1)),
    }
def name(l): return meta.get(l, {}).get("name", "?")
def macro_of(l): return meta.get(l, {}).get("macro", re.match(r"([MN]\d+)-", l).group(1) if re.match(r"([MN]\d+)-", l) else l)

# ---- trait 멤버십 (positive 구성 = required + optional) ----
micro_traits = defaultdict(set)   # 라벨 -> 소속 trait_id 집합
defines = set()                   # 어떤 trait를 '정의'하는 라벨(required/optional)
forbidden = set()                 # 어떤 trait를 '무효화/감점'하는 라벨
trait_name = {}
for t in traits:
    tid = t["trait_id"]; trait_name[tid] = t["trait_name"]
    for k in ("required", "optional"):
        for l in t.get(k, []):
            micro_traits[l].add(tid); defines.add(l)
    for l in t.get("hard_forbidden", []):
        forbidden.add(l)
    for s in t.get("soft_forbidden", []):
        forbidden.add(s["label"])

# ---- 데이터 분리 (baseline과 동일 규칙: clean/blank=양성, hard_negative 제외) ----
pos_by_label = defaultdict(list)
for r in train_raw:
    if r.get("data_type") != "hard_negative":
        pos_by_label[r["label_id"]].append(r["text"])

X_train, y_train, X_test, y_test = [], [], [], []
for lid, texts in pos_by_label.items():
    ts = texts[:]; random.shuffle(ts)
    cut = max(1, int(len(ts) * 0.25))
    for t in ts[:cut]: X_test.append(t);  y_test.append(lid)
    for t in ts[cut:]: X_train.append(t); y_train.append(lid)

vec = TfidfVectorizer(analyzer="char_wb", ngram_range=(2, 5), min_df=2, sublinear_tf=True)
Xtr = vec.fit_transform(X_train); Xte = vec.transform(X_test)
clf = LogisticRegression(max_iter=2000, C=8.0, class_weight="balanced")
clf.fit(Xtr, y_train)
pred = clf.predict(Xte)

labels_sorted = sorted(pos_by_label)
f1_per = dict(zip(labels_sorted,
                  f1_score(y_test, pred, labels=labels_sorted, average=None, zero_division=0)))

# ---- 혼동 집계 ----
confusion = Counter()           # (true, pred) -> n  (true != pred)
test_total = Counter()          # true -> 테스트 샘플 수
err_total = Counter()           # true -> 오분류 수
for t, p in zip(y_test, pred):
    test_total[t] += 1
    if t != p:
        confusion[(t, p)] += 1
        err_total[t] += 1

# =====================================================================
# (A) ORPHAN: 학습데이터 있는데 trait 미연결
# =====================================================================
orphans = []
for l in labels_sorted:
    if l in defines:
        continue
    # 갈 곳 추천: 가장 많이 혼동되는 상대의 trait
    partners = sorted([(n, b) for (a, b), n in confusion.items() if a == l],
                      key=lambda x: -x[0])
    home = ""
    for _, b in partners:
        if micro_traits.get(b):
            home = f"{b}({name(b)})→{'/'.join(sorted(micro_traits[b]))}"
            break
    role = "forbidden-only" if l in forbidden else "완전 미연결"
    orphans.append((l, f1_per.get(l, 0), test_total.get(l, 0), role, home))

# =====================================================================
# (B) 과세분: 같은 macro 안에서 서로 혼동
# =====================================================================
macro_groups = defaultdict(list)
for l in labels_sorted:
    macro_groups[macro_of(l)].append(l)

macro_rows = []
for mg, members in macro_groups.items():
    if len(members) < 2:
        continue
    f1s = [f1_per[l] for l in members]
    mean_f1 = sum(f1s) / len(f1s)
    # 내부 혼동량: 이 macro 라벨들의 오분류 중 같은 macro 형제로 간 비율
    grp_err = sum(err_total[l] for l in members)
    internal = sum(n for (a, b), n in confusion.items()
                   if a in members and b in members)
    int_ratio = internal / grp_err if grp_err else 0
    macro_rows.append((mg, len(members), mean_f1, int_ratio, grp_err, members))
macro_rows.sort(key=lambda x: (x[2], -x[3]))   # 낮은 F1 + 높은 내부혼동 우선

# =====================================================================
# (C) trait 경계 혼동: 다른 trait 소속인데 혼동 (공유 trait 없음)
# =====================================================================
cross = []
for (a, b), n in confusion.items():
    ta, tb = micro_traits.get(a, set()), micro_traits.get(b, set())
    if ta and tb and not (ta & tb) and macro_of(a) != macro_of(b):
        cross.append((n, a, b, ta, tb))
cross.sort(key=lambda x: -x[0])

# =====================================================================
# 리포트
# =====================================================================
out = []
W = out.append
W("# Taxonomy 감사 리포트 — 라벨 정리 + trait 군집 재검토")
W("")
W("> TF-IDF 분류기 혼동행렬 기반 1차 감사 (의미 임베딩 없는 보수적 신호).")
W("> **'병합/재배치 후보'를 근거와 함께 제시할 뿐, 자동 결정이 아니다. 최종 판단은 도메인 몫.**")
W("> 현재 데이터는 표면(어휘) 분리성만 측정 — 맥락 의존 구분은 hard 평가셋에서 별도 검증 필요.")
W("")
W(f"- 평가 라벨 {len(labels_sorted)}개 · 테스트 {len(y_test)}문장")
W(f"- Orphan(trait 미연결) **{len(orphans)}개** · 과세분 후보 macro **{sum(1 for r in macro_rows if r[2]<0.55)}개** · trait 경계 혼동쌍 **{len(cross)}개**")
W("")

# --- A ---
W("## A. Orphan — 학습데이터는 있으나 어떤 trait에도 안 묶임")
W("")
W("이 라벨들은 분류기가 (잘) 맞혀도 **trait로 집계되지 않아 결과에 안 쓰임**. 매핑하거나 폐기 결정 필요.")
W("")
W("| 라벨 | 이름 | F1 | 테스트n | 상태 | 추천 소속(최다혼동 상대 기준) |")
W("|------|------|----|--------|------|------------------|")
for l, f1, n, role, home in sorted(orphans, key=lambda x: -x[1]):
    W(f"| {l} | {name(l)} | {f1:.2f} | {n} | {role} | {home or '—'} |")
W("")

# --- B ---
W("## B. 과세분(over-segmentation) — 같은 macro 안에서 서로 뭉갬")
W("")
W("`내부혼동률` = 그 macro 라벨들의 오분류 중 **같은 macro 형제로 잘못 간 비율**. 높을수록 ")
W("\"모델이 못 한다\"가 아니라 \"라벨이 원래 안 갈린다\" → **병합 또는 2단(macro→micro) 분류** 후보.")
W("")
W("| macro | 멤버수 | 평균F1 | 내부혼동률 | 멤버(F1) |")
W("|-------|--------|--------|-----------|----------|")
for mg, k, mf1, ir, ge, members in macro_rows:
    flag = " ⚠️" if (mf1 < 0.55 and ir >= 0.4) else ""
    ms = ", ".join(f"{l}({f1_per[l]:.2f})" for l in sorted(members, key=lambda x: -f1_per[x]))
    W(f"| **{mg}**{flag} | {k} | {mf1:.2f} | {ir:.0%} | {ms} |")
W("")
W("⚠️ = 평균F1<0.55 & 내부혼동률≥40% → 우선 병합/계층화 검토 대상")
W("")

# --- C ---
W("## C. trait 경계 혼동 — 다른 trait 소속인데 체계적 혼동")
W("")
W("공유 trait이 없는 두 라벨이 서로 혼동됨 = 분류기가 **서로 다른 리더십 신호를 같은 것으로** 봄.")
W("라벨 정의가 겹치거나, trait 배치가 어긋났을 신호. (n=혼동 횟수)")
W("")
W("| n | A 라벨 | A trait | → | B 라벨 | B trait |")
W("|---|--------|---------|---|--------|---------|")
for n, a, b, ta, tb in cross[:25]:
    W(f"| {n} | {a} {name(a)} | {'/'.join(sorted(ta))} | → | {b} {name(b)} | {'/'.join(sorted(tb))} |")
W("")

# --- 종합 제안 ---
W("## D. 수정 taxonomy 초안 (사람 검수용)")
W("")
W("### D-1. 병합/계층화 검토 (B에서 ⚠️)")
for mg, k, mf1, ir, ge, members in macro_rows:
    if mf1 < 0.55 and ir >= 0.4:
        W(f"- **{mg}** ({k}개, 평균F1 {mf1:.2f}, 내부혼동 {ir:.0%}): "
          f"{', '.join(name(l) for l in members)} → 1개 macro 라벨로 병합 또는 2단 분류")
W("")
W("### D-2. Orphan 처리")
mapped = [o for o in orphans if o[4]]
W(f"- 매핑 후보 있음 {len(mapped)}개 / 완전 고립 {len(orphans)-len(mapped)}개")
W("- 고F1 orphan(N38~N43 등)은 '버리기 아까운' 라벨 → 신규 trait 신설 or 기존 trait 편입 검토")
W("")
W("### D-3. trait 배치 재검토")
W(f"- C의 경계 혼동쌍 {len(cross)}개 중 상위 → 두 라벨이 정말 다른 trait인지, 정의가 겹치는지 확인")
W("")

open(P("docs/taxonomy_audit.md"), "w", encoding="utf-8").write("\n".join(out))

# ---- 콘솔 요약 ----
print(f"라벨 {len(labels_sorted)} · 테스트 {len(y_test)}")
print(f"[A] Orphan: {len(orphans)}개 (고립 {len(orphans)-len(mapped)} / 매핑후보 {len(mapped)})")
print(f"[B] 과세분 ⚠️ macro: {[r[0] for r in macro_rows if r[2]<0.55 and r[3]>=0.4]}")
print(f"[C] trait 경계 혼동쌍: {len(cross)}개 (상위: " +
      ", ".join(f"{a}→{b}({n})" for n, a, b, _, _ in cross[:5]) + ")")
print("\n리포트: docs/taxonomy_audit.md")
