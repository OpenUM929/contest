# -*- coding: utf-8 -*-
"""
Taxonomy 단일 진실원(single source of truth).

v4 라벨/trait 정의를 한 곳에서 로드하고, deprecated→생존(canon) 맵과
구조 불변식 점검을 제공한다. eval_hard / bakeoff / build 스크립트에
복붙돼 있던 canon 로직을 여기로 일원화한다 — 라벨이 늘어나도 한 곳만 보면 됨.

사용:
    from taxonomy import Taxonomy
    tax = Taxonomy.load()
    tax.canon("M09-01")            # -> "M08-02" (deprecated면 생존 라벨로)
    tax.orphans()                  # 학습데이터 있지만 어떤 trait에도 안 붙은 라벨
    issues = tax.check_invariants()  # list[str], 비어있으면 통과
"""
import json
import os
from collections import defaultdict

BASE = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))


def _P(*a):
    return os.path.join(BASE, *a)


def _load(rel):
    with open(_P(rel), encoding="utf-8") as f:
        return json.load(f)


# v4 우선, 없으면 구버전으로 폴백 — 한 곳에서만 분기
MICRO_FILES = [
    ("dataset/ori/positive_micro_labels_v4.json", "data/micro_labels/positive_micro_labels.json"),
    ("dataset/ori/negative_micro_labels_v4.json", "data/micro_labels/negative_micro_labels.json"),
]
TRAIT_FILES = ["data/traits/trait_definitions_v4.json", "data/traits/trait_definitions.json"]
TRAINING_FILE = "dataset/ori/training_data_all_labels.json"


class Taxonomy:
    def __init__(self, micros, traits, training):
        self.micros = micros            # label_id -> dict
        self.traits = traits            # trait_id -> dict
        self._training = training        # list of {label_id, text, data_type}
        self._canon = self._build_canon()

    # ---------- 로딩 ----------
    @classmethod
    def load(cls):
        micros = {}
        for primary, fallback in MICRO_FILES:
            rel = primary if os.path.exists(_P(primary)) else fallback
            for m in _load(rel)["micro_labels"]:
                micros[m["label_id"]] = m
        traits = {}
        tpath = next((t for t in TRAIT_FILES if os.path.exists(_P(t))), None)
        for t in _load(tpath)["traits"]:
            traits[t["trait_id"]] = t
        training = _load(TRAINING_FILE) if os.path.exists(_P(TRAINING_FILE)) else []
        return cls(micros, traits, training)

    # ---------- canon (deprecated -> 생존, 체인 해소) ----------
    def _build_canon(self):
        direct = {lid: m["superseded_by"] for lid, m in self.micros.items()
                  if m.get("superseded_by")}
        resolved = {}
        for lid in direct:
            seen, cur = set(), lid
            while cur in direct and cur not in seen:
                seen.add(cur)
                cur = direct[cur]
            resolved[lid] = cur
        return resolved

    def canon(self, label_id):
        if not label_id:
            return label_id
        return self._canon.get(label_id, label_id)

    # ---------- 파생 집합 ----------
    def deprecated_ids(self):
        return {lid for lid, m in self.micros.items() if m.get("deprecated")}

    def trait_referenced_ids(self):
        """어떤 trait의 required/optional에 등장하는 모든 micro 라벨."""
        ref = set()
        for t in self.traits.values():
            ref.update(t.get("required", []))
            ref.update(t.get("optional", []))
        return ref

    def labels_with_training(self):
        return {self.canon(r["label_id"]) for r in self._training
                if r.get("data_type") != "hard_negative"}

    def orphans(self):
        """학습데이터가 있는데 살아있고(미deprecated) 어떤 trait에도 안 붙은 라벨."""
        ref = self.trait_referenced_ids()
        dep = self.deprecated_ids()
        out = []
        for lid in sorted(self.labels_with_training()):
            if lid in self.micros and lid not in dep and lid not in ref:
                out.append(lid)
        return out

    # ---------- 불변식 ----------
    def check_invariants(self):
        issues = []

        # I1: 모든 trait은 anchor >= 1 (공유 hub만으로 점화 금지)
        for tid, t in self.traits.items():
            anc = t.get("anchor", [])
            if not anc:
                issues.append(f"[I1 anchor] {tid} '{t.get('trait_name','')}' 앵커 0개")
            else:
                for a in anc:
                    if a not in self.micros:
                        issues.append(f"[I1 anchor] {tid} 앵커 {a} 가 micro 정의에 없음")
                    elif self.micros[a].get("deprecated"):
                        issues.append(f"[I1 anchor] {tid} 앵커 {a} 가 deprecated")
                    elif a not in t.get("required", []):
                        issues.append(f"[I1 anchor] {tid} 앵커 {a} 가 required에 없음")

        # I2: orphan = 0
        for lid in self.orphans():
            issues.append(f"[I2 orphan] {lid} '{self.micros[lid].get('label_name','')}' 미연결(학습데이터 보유)")

        # I3: deprecated 무결성 — superseded_by 가 살아있는 라벨을 가리켜야
        for lid in self.deprecated_ids():
            sup = self.micros[lid].get("superseded_by")
            if not sup:
                issues.append(f"[I3 deprecated] {lid} deprecated인데 superseded_by 없음")
            elif sup not in self.micros:
                issues.append(f"[I3 deprecated] {lid} -> {sup} 가 존재하지 않음")
            elif self.micros[sup].get("deprecated"):
                issues.append(f"[I3 deprecated] {lid} -> {sup} 도 deprecated (체인 미해소)")

        # I4: trait 참조 라벨이 실존(deprecated 직접 참조 경고 포함)
        for tid, t in self.traits.items():
            for field in ("required", "optional", "hard_forbidden"):
                for lid in t.get(field, []):
                    if lid not in self.micros:
                        issues.append(f"[I4 ref] {tid}.{field} {lid} micro 정의에 없음")
                    elif self.micros[lid].get("deprecated"):
                        issues.append(f"[I4 ref] {tid}.{field} {lid} deprecated 라벨 직접 참조 (canon={self.canon(lid)})")
            for sf in t.get("soft_forbidden", []):
                lid = sf.get("label") if isinstance(sf, dict) else sf
                if lid and lid not in self.micros:
                    issues.append(f"[I4 ref] {tid}.soft_forbidden {lid} micro 정의에 없음")

        # I5: label_id 중복(로딩 시 dedupe되므로 raw 카운트로 점검)
        seen = defaultdict(int)
        for primary, fallback in MICRO_FILES:
            rel = primary if os.path.exists(_P(primary)) else fallback
            for m in _load(rel)["micro_labels"]:
                seen[m["label_id"]] += 1
        for lid, n in seen.items():
            if n > 1:
                issues.append(f"[I5 dup] label_id {lid} {n}회 중복 정의")

        # I6: 동일 label_name 중복(살아있는 라벨끼리) — 과세분/복제 탐지
        by_name = defaultdict(list)
        for lid, m in self.micros.items():
            if not m.get("deprecated"):
                by_name[m.get("label_name", "")].append(lid)
        for name, ids in by_name.items():
            if name and len(ids) > 1:
                issues.append(f"[I6 dupname] '{name}' 동일명 라벨 다수: {ids}")

        return issues

    # ---------- 역할 자동판정(워크플로용) ----------
    def fanout(self):
        """각 micro가 몇 개 trait의 required/optional에 등장하는지."""
        fo = defaultdict(int)
        for t in self.traits.values():
            for lid in set(t.get("required", [])) | set(t.get("optional", [])):
                fo[lid] += 1
        return fo

    def suggested_role(self, label_id):
        """fan-out 기반 역할 제안: 1=anchor후보, 2~3=discriminative, 4+=supporting(hub)."""
        n = self.fanout().get(label_id, 0)
        if n == 0:
            return "unassigned"
        if n == 1:
            return "anchor"
        if n <= 3:
            return "discriminative"
        return "supporting"


if __name__ == "__main__":
    tax = Taxonomy.load()
    print(f"micros={len(tax.micros)} traits={len(tax.traits)} "
          f"deprecated={len(tax.deprecated_ids())} orphans={len(tax.orphans())}")
