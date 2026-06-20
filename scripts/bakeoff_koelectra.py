# -*- coding: utf-8 -*-
"""
모델 bake-off: KoELECTRA(의미 임베딩) vs TF-IDF(floor) — 같은 Hard 평가셋.
KoELECTRA를 frozen feature extractor로 사용(임베딩) → LogReg.
CPU 속도 위해 라벨당 학습샘플 캡.
"""
import json, os, random
from collections import defaultdict
import numpy as np
BASE = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
def P(*a): return os.path.join(BASE, *a)
def load(p): return json.load(open(P(p), encoding="utf-8"))
random.seed(42)
REJECT_GATE = 0.35
PER_LABEL_CAP = 25

canon = {}
for f in ("dataset/ori/positive_micro_labels_v4.json", "dataset/ori/negative_micro_labels_v4.json"):
    if os.path.exists(P(f)):
        for m in load(f)["micro_labels"]:
            if m.get("superseded_by"): canon[m["label_id"]] = m["superseded_by"]
def C(l): return canon.get(l, l) if l else l

# ---- 학습 데이터 (canon, 라벨당 캡) ----
train = load("dataset/ori/training_data_all_labels.json")
by_label = defaultdict(list)
for r in train:
    if r.get("data_type") != "hard_negative":
        by_label[C(r["label_id"])].append(r["text"])
X, y = [], []
for lid, texts in by_label.items():
    random.shuffle(texts)
    for t in texts[:PER_LABEL_CAP]:
        X.append(t); y.append(lid)
print(f"학습 샘플 {len(X)} (라벨당 최대 {PER_LABEL_CAP})")

# ---- KoELECTRA 임베딩 ----
import sys, torch
from transformers import AutoTokenizer, AutoModel
MODEL = sys.argv[1] if len(sys.argv) > 1 else "monologg/koelectra-base-v3-discriminator"
print(f"모델 로드: {MODEL} ...")
tok = AutoTokenizer.from_pretrained(MODEL)
model = AutoModel.from_pretrained(MODEL); model.eval()

@torch.no_grad()
def embed(texts, bs=32):
    out = []
    for i in range(0, len(texts), bs):
        b = texts[i:i+bs]
        enc = tok(b, padding=True, truncation=True, max_length=64, return_tensors="pt")
        h = model(**enc).last_hidden_state            # (B,T,H)
        mask = enc["attention_mask"].unsqueeze(-1).float()
        emb = (h * mask).sum(1) / mask.sum(1).clamp(min=1e-9)   # mean pooling
        out.append(emb.cpu().numpy())
    return np.vstack(out)

print("학습 임베딩 계산 중...")
Xemb = embed(X)
from sklearn.linear_model import LogisticRegression
clf = LogisticRegression(max_iter=2000, C=8.0, class_weight="balanced")
clf.fit(Xemb, y)

# ---- Hard 채점 ----
cases = load("data/eval/hard_eval_set.json")["cases"]
He = embed([c["text"] for c in cases])
preds = clf.predict(He); probas = clf.predict_proba(He).max(axis=1)

by_cat = defaultdict(lambda: [0, 0])
for c, p, pr in zip(cases, preds, probas):
    ok = (pr < REJECT_GATE) if c["gold"] is None else (C(p) == C(c["gold"]))
    by_cat[c["category"]][0] += int(ok); by_cat[c["category"]][1] += 1

print(f"\n=== Hard 평가셋 · KoELECTRA 임베딩 + LogReg ===\n")
print(f"{'범주':<22}{'정답/전체':>10}{'정확도':>9}")
tc = tn = 0
for cat in ("mirror_flip", "reversal", "cross_sentence_intent", "negation", "past_tense_exclusion", "hub_disambiguation"):
    c, n = by_cat[cat]; tc += c; tn += n
    print(f"{cat:<22}{f'{c}/{n}':>10}{(c/n*100 if n else 0):>8.0f}%")
print("─"*41)
print(f"{'전체':<22}{f'{tc}/{tn}':>10}{tc/tn*100:>8.0f}%")
print("\n(비교: TF-IDF floor 전체 42%)")
