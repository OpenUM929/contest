# -*- coding: utf-8 -*-
"""
Baseline 분류기 PoC (TF-IDF floor)
==================================
KOTE식 평면 분류기가 178개 라벨을 실제로 얼마나 가르는지 '보수적 하한'을 측정.
- 의미 임베딩 없는 char n-gram TF-IDF + LogisticRegression → 실제 KcELECTRA는 이 위.
- clean/blank = 양성 학습, hard_negative = 거부(rejection) 테스트.
- 라벨별 F1을 A/B/C 버킷과 교차표로 출력 → 버킷 경험적 검증 + A버킷 orphan 보정.
"""
import json, os, re, random
from collections import Counter, defaultdict
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.linear_model import LogisticRegression
from sklearn.metrics import f1_score

random.seed(42)
BASE = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
def P(*a): return os.path.join(BASE, *a)

train_raw = json.load(open(P("dataset/ori/training_data_all_labels.json"), encoding="utf-8"))

# ---- bucket 매핑: classify 리포트(md)에서 label_id -> bucket 파싱 ----
bucket = {}
md = open(P("docs/label_ab_classification.md"), encoding="utf-8").read()
for m in re.finditer(r"\|\s*([MN]\d+-\d+)\s*\|[^|]*\|\s*(pos|neg)\s*\|\s*(\d+)\s*\|\s*([ABC])\s*\|", md):
    bucket[m.group(1)] = m.group(4)

# ---- 데이터 분리 ----
pos_by_label = defaultdict(list)   # 양성(clean/blank)
hard_neg = []                      # 거부 테스트
for r in train_raw:
    dt = r.get("data_type")
    if dt == "hard_negative":
        hard_neg.append(r)
    else:  # clean 또는 blank
        pos_by_label[r["label_id"]].append(r["text"])

# 라벨별 75/25 분할 (재현 가능)
X_train, y_train, X_test, y_test = [], [], [], []
for lid, texts in pos_by_label.items():
    ts = texts[:]; random.shuffle(ts)
    cut = max(1, int(len(ts) * 0.25))
    test, tr = ts[:cut], ts[cut:]
    for t in tr:   X_train.append(t); y_train.append(lid)
    for t in test: X_test.append(t);  y_test.append(lid)

print(f"라벨 {len(pos_by_label)}개 | train {len(X_train)} / test {len(X_test)} | hard_neg {len(hard_neg)}")

# ---- 벡터화 + 학습 ----
vec = TfidfVectorizer(analyzer="char_wb", ngram_range=(2, 5), min_df=2, sublinear_tf=True)
Xtr = vec.fit_transform(X_train)
Xte = vec.transform(X_test)
clf = LogisticRegression(max_iter=2000, C=8.0, class_weight="balanced")
clf.fit(Xtr, y_train)

pred = clf.predict(Xte)
acc = sum(p == y for p, y in zip(pred, y_test)) / len(y_test)
macro_f1 = f1_score(y_test, pred, average="macro", zero_division=0)
print(f"\n전체 Top-1 정확도: {acc:.3f} | macro-F1: {macro_f1:.3f}")

# ---- 라벨별 F1 ----
labels_sorted = sorted(pos_by_label)
f1_per = dict(zip(labels_sorted,
                  f1_score(y_test, pred, labels=labels_sorted, average=None, zero_division=0)))

def agg(pred_filter):
    vals = [f1_per[l] for l in labels_sorted if pred_filter(l)]
    return (sum(vals) / len(vals), len(vals)) if vals else (0, 0)

# ---- 교차표: 버킷 × type ----
def is_pos(l): return l.startswith("M")
print("\n=== 라벨별 평균 F1 (교차표) ===")
print(f"{'버킷':<5}{'전체F1':>8}{'n':>4}   {'긍정F1':>8}{'n':>4}   {'부정F1':>8}{'n':>4}")
for b in ("A", "C", "B"):
    a_all = agg(lambda l: bucket.get(l) == b)
    a_pos = agg(lambda l: bucket.get(l) == b and is_pos(l))
    a_neg = agg(lambda l: bucket.get(l) == b and not is_pos(l))
    print(f"{b:<5}{a_all[0]:>8.3f}{a_all[1]:>4}   {a_pos[0]:>8.3f}{a_pos[1]:>4}   {a_neg[0]:>8.3f}{a_neg[1]:>4}")
pos_overall = agg(is_pos); neg_overall = agg(lambda l: not is_pos(l))
print(f"{'─'*40}")
print(f"{'긍정 전체':<5}{pos_overall[0]:>8.3f}{pos_overall[1]:>4}")
print(f"{'부정 전체':<5}{neg_overall[0]:>8.3f}{neg_overall[1]:>4}")

# ---- hard_negative 거부 테스트 ----
hn_texts = [r["text"] for r in hard_neg]
hn_true_lbl = [r["label_id"] for r in hard_neg]  # 이 라벨로 '오인'하면 실패
hn_pred = clf.predict(vec.transform(hn_texts))
hn_proba = clf.predict_proba(vec.transform(hn_texts)).max(axis=1)
false_accept = sum(p == t for p, t in zip(hn_pred, hn_true_lbl)) / len(hn_texts)
print(f"\n=== hard_negative 거부 테스트 ({len(hn_texts)}개) ===")
print(f"오인율(반례를 해당 라벨로 분류): {false_accept:.3f}  (낮을수록 좋음)")
print(f"평균 최대확신도: {hn_proba.mean():.3f}  (낮을수록 거부 잘함)")

# ---- A버킷 orphan 보정: 구조신호=0 라벨의 '진짜' 분리도 ----
traits = json.load(open(P("data/traits/trait_definitions.json"), encoding="utf-8"))["traits"]
in_trait = set()
for t in traits:
    for k in ("required", "optional", "hard_forbidden"):
        in_trait.update(t.get(k, []))
    for s in t.get("soft_forbidden", []):
        in_trait.add(s["label"])
print("\n=== A버킷 라벨: 경험적 F1 (orphan = trait 미연결) ===")
a_labels = [l for l in labels_sorted if bucket.get(l) == "A"]
for l in sorted(a_labels, key=lambda x: -f1_per[x]):
    tag = "" if l in in_trait else "  [orphan]"
    print(f"  {l}  F1={f1_per[l]:.2f}{tag}")

# ---- C버킷 세분화: 분류기 OK vs 규칙 필요 ----
print("\n=== C버킷 세분화 (73개) ===")
c_labels = [l for l in labels_sorted if bucket.get(l) == "C"]
c_ok = [l for l in c_labels if f1_per[l] >= 0.70]
c_weak = [l for l in c_labels if f1_per[l] < 0.50]
print(f"  분류기 단독 OK (F1≥0.70): {len(c_ok)}개")
print(f"  규칙 보정 필요 (F1<0.50): {len(c_weak)}개  예: {', '.join(c_weak[:8])}")

# ---- 리포트 저장 ----
rows = sorted(labels_sorted, key=lambda l: (bucket.get(l, "Z"), -f1_per[l]))
out = ["# Baseline 분류기 PoC 리포트 (TF-IDF floor)", "",
       f"> char n-gram TF-IDF + LogisticRegression · 의미 임베딩 없는 **보수적 하한**",
       f"> 실제 KcELECTRA(의미 임베딩)는 이 수치를 상회함", "",
       "## 종합", "",
       f"- 전체 Top-1 정확도: **{acc:.3f}**, macro-F1: **{macro_f1:.3f}**",
       f"- 긍정 평균 F1: **{pos_overall[0]:.3f}** ({pos_overall[1]}개) / 부정 평균 F1: **{neg_overall[0]:.3f}** ({neg_overall[1]}개)",
       f"- hard_negative 오인율: **{false_accept:.3f}** / 평균확신도 {hn_proba.mean():.3f}", "",
       "## 버킷 × type 평균 F1", "",
       "| 버킷 | 전체 F1 | 긍정 F1 | 부정 F1 |",
       "|------|---------|---------|---------|"]
for b in ("A", "C", "B"):
    a_all = agg(lambda l: bucket.get(l) == b)
    a_pos = agg(lambda l: bucket.get(l) == b and is_pos(l))
    a_neg = agg(lambda l: bucket.get(l) == b and not is_pos(l))
    out.append(f"| {b} | {a_all[0]:.3f} (n={a_all[1]}) | {a_pos[0]:.3f} (n={a_pos[1]}) | {a_neg[0]:.3f} (n={a_neg[1]}) |")
out += ["", "## 라벨별 F1", "", "| 라벨 | 버킷 | type | F1 | orphan |",
        "|------|------|------|------|------|"]
for l in rows:
    out.append(f"| {l} | {bucket.get(l,'?')} | {'pos' if is_pos(l) else 'neg'} | {f1_per[l]:.2f} | {'' if l in in_trait else 'Y'} |")
open(P("docs/baseline_classifier_report.md"), "w", encoding="utf-8").write("\n".join(out))
print("\n리포트 저장: docs/baseline_classifier_report.md")
