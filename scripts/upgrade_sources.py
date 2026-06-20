# -*- coding: utf-8 -*-
"""
Phase1 출처 정제: 레지스트리/causal의 각 source에
  evidence_grade(M/S/E/R/B) · peer_reviewed(bool) · doi(추출가능시)
를 부여하고, 2차 경로(blog/researchgate/academia/studocu 등)를 플래그.

비파괴: 기존 필드 유지, 누락 필드만 추가. 실행 후 플래그된 항목을 수동으로
1차 출처로 교체한다.
실행: python -X utf8 scripts/upgrade_sources.py
"""
import json
import os
import re

BASE = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
FILES = ["data/evidence/leadership_evidence_registry.json",
         "data/evidence/causal_rationale.json"]

SECONDARY = ("leadershipahoy.com", "researchgate.net", "academia.edu",
             "studocu.com", "scribd.com", "wikipedia.org", "wordpress.com",
             "statisticssolutions.com", "linkedin.com", "doaj.org")
GRADE_BY_TYPE = {"meta-analysis": "M", "SLR": "S", "review": "R", "scale": "E",
                 "primary": "E", "framework": "B"}
DOI_RE = re.compile(r"(10\.\d{4,9}/[^\s\"<>]+)")


def doi_from_url(url):
    m = DOI_RE.search(url or "")
    if not m:
        return ""
    return m.group(1).rstrip(").")


def is_secondary(url):
    return any(d in (url or "") for d in SECONDARY)


def upgrade_source(s):
    changed = False
    if "evidence_grade" not in s:
        s["evidence_grade"] = GRADE_BY_TYPE.get(s.get("type", ""), "R")
        changed = True
    if "peer_reviewed" not in s:
        s["peer_reviewed"] = not is_secondary(s.get("url", ""))
        changed = True
    if "doi" not in s:
        s["doi"] = doi_from_url(s.get("url", ""))
        changed = True
    return changed


flagged = []
for rel in FILES:
    path = os.path.join(BASE, rel)
    with open(path, encoding="utf-8") as f:
        data = json.load(f)

    def walk_sources(container, ctx):
        for s in container:
            upgrade_source(s)
            if not s["peer_reviewed"] or s["evidence_grade"] == "B":
                flagged.append((ctx, s.get("cite", "?"), s.get("url", ""),
                                s["evidence_grade"], s["peer_reviewed"]))

    if "constructs" in data and isinstance(data["constructs"], list):  # registry
        for c in data["constructs"]:
            walk_sources(c.get("sources", []), c["id"])
    elif "constructs" in data and isinstance(data["constructs"], dict):  # causal
        for cid, c in data["constructs"].items():
            ds = c.get("dimensions_source")
            if ds:
                upgrade_source(ds)
                if not ds["peer_reviewed"] or ds["evidence_grade"] == "B":
                    flagged.append((cid, ds.get("cite", "?"), ds.get("url", ""),
                                    ds["evidence_grade"], ds["peer_reviewed"]))

    with open(path, "w", encoding="utf-8") as f:
        json.dump(data, f, ensure_ascii=False, indent=2)

print("출처 필드 부여 완료 (evidence_grade/peer_reviewed/doi)\n")
print(f"[수동 교체 필요 — 2차경로 또는 grade=B] {len(flagged)}건")
for ctx, cite, url, g, pr in flagged:
    print(f"  - [{ctx}] grade={g} peer={pr} | {cite}\n      {url}")
