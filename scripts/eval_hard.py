# -*- coding: utf-8 -*-
"""
Hard 평가셋 채점 — 맥락 의존 케이스에서 분류기 한계를 처음으로 측정.
모델 bake-off의 공통 채점기(harness): 어떤 분류기든 predict/predict_proba만 있으면 됨.
"""
import json, os, random, argparse
from collections import defaultdict
BASE = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
def P(*a): return os.path.join(BASE, *a)
def load(p): return json.load(open(P(p), encoding="utf-8"))

REJECT_GATE = 0.35

# canon map: deprecated -> survivor (v4)
canon = {}
for f in ("dataset/ori/positive_micro_labels_v4.json", "dataset/ori/negative_micro_labels_v4.json"):
    if os.path.exists(P(f)):
        for m in load(f)["micro_labels"]:
            if m.get("superseded_by"):
                canon[m["label_id"]] = m["superseded_by"]
def C(l): return canon.get(l, l) if l else l

def train_tfidf():
    from sklearn.feature_extraction.text import TfidfVectorizer
    from sklearn.linear_model import LogisticRegression
    random.seed(42)
    train = load("dataset/ori/training_data_all_labels.json")
    X, y = [], []
    for r in train:
        if r.get("data_type") != "hard_negative":
            X.append(r["text"]); y.append(C(r["label_id"]))   # 학습도 canon 라벨로
    vec = TfidfVectorizer(analyzer="char_wb", ngram_range=(2, 5), min_df=2, sublinear_tf=True)
    clf = LogisticRegression(max_iter=2000, C=8.0, class_weight="balanced")
    Xv = vec.fit_transform(X); clf.fit(Xv, y)
    def predict(texts):
        M = vec.transform(texts)
        return clf.predict(M), clf.predict_proba(M).max(axis=1)
    return predict, "TF-IDF+LogReg (floor)"

def main(model="tfidf"):
    predict, name = train_tfidf()   # bake-off 시 여기 분기 추가
    cases = load("data/eval/hard_eval_set.json")["cases"]
    texts = [c["text"] for c in cases]
    preds, probas = predict(texts)

    by_cat = defaultdict(lambda: [0, 0])   # [correct, total]
    rows = []
    for c, p, pr in zip(cases, preds, probas):
        gold = c["gold"]
        if gold is None:                    # 거부해야 정답
            ok = pr < REJECT_GATE
        else:
            ok = C(p) == C(gold)
        by_cat[c["category"]][0] += int(ok)
        by_cat[c["category"]][1] += 1
        rows.append((c["id"], c["category"], gold, C(p), round(float(pr), 2), ok))

    print(f"=== Hard 평가셋 채점 · 모델: {name} ===\n")
    print(f"{'범주':<22}{'정답/전체':>10}{'정확도':>9}")
    tot_c = tot_n = 0
    for cat in ("mirror_flip", "reversal", "cross_sentence_intent", "negation", "past_tense_exclusion", "hub_disambiguation"):
        c, n = by_cat[cat]
        tot_c += c; tot_n += n
        print(f"{cat:<22}{f'{c}/{n}':>10}{c/n*100:>8.0f}%")
    print(f"{'─'*41}")
    print(f"{'전체':<22}{f'{tot_c}/{tot_n}':>10}{tot_c/tot_n*100:>8.0f}%")

    print("\n=== 오답 상세 ===")
    for cid, cat, gold, pred, pr, ok in rows:
        if not ok:
            print(f"  {cid} [{cat}] gold={gold} → pred={pred} (conf={pr})")

if __name__ == "__main__":
    ap = argparse.ArgumentParser(); ap.add_argument("--model", default="tfidf"); a = ap.parse_args()
    main(a.model)
