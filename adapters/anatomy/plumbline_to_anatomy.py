#!/usr/bin/env python3
"""plumbline_to_anatomy.py — feed Plumbline governance results into an
Architecture Anatomy catalog as a governance overlay.

Lives in the Plumbline repo at adapters/anatomy/ (the referee owns its own
output formats; no new repo).

What it does
------------
1. Reads one or more Plumbline reports (.plumbline/report.json), each tagged
   with the repo/system it came from.
2. Reads an Anatomy catalog (the JSON single source of truth).
3. Reads a mapping file that links report sources to catalog node ids —
   because Plumbline knows repos and Anatomy knows components, and only a
   human knows that repo 'cloudintelmatrix' IS node 'cim-api'.
4. Writes an annotated copy of the catalog:
   - each mapped node gains a `gov` block: {status, fails, warns, gates, asOf}
   - `meta.governance` records run provenance
   - a 'GOV' scope ring is appended to `meta.scopes` listing every node whose
     status is 'fail', so today's Anatomy build renders failing systems as a
     compliance ring with ZERO renderer changes. (A proper per-node stain is
     the v0.1 renderer patch — see ROADMAP.md.)

Usage
-----
  python3 plumbline_to_anatomy.py \
      --catalog architecture-catalog.json \
      --mapping mapping.yaml \
      --report plumbline:path/to/plumbline/report.json \
      --report cloudintelmatrix:path/to/cim/report.json \
      --out architecture-catalog.gov.json

Then open Anatomy with ?catalog=architecture-catalog.gov.json.

No dependencies beyond PyYAML (already a Plumbline dependency).
"""

from __future__ import annotations

import argparse
import copy
import json
import sys
from datetime import datetime, timezone
from pathlib import Path

import yaml

GOV_RING = {"id": "GOV", "t": "Governance: failing gates", "c": "#e05252"}


def load_reports(pairs: list[str]) -> dict[str, dict]:
    """Each pair is 'source_name:path'. Returns {source_name: report_dict}."""
    reports = {}
    for pair in pairs:
        name, _, path = pair.partition(":")
        if not path:
            sys.exit(f"--report must be name:path, got '{pair}'")
        reports[name] = json.loads(Path(path).read_text(encoding="utf-8"))
    return reports


def summarize(report: dict) -> dict:
    """Collapse a Plumbline report into a node-sized governance verdict."""
    fails, warns, gates = 0, 0, {}
    for r in report.get("results", []):
        gates[r["gate"]] = r["status"]
        if r["status"] == "fail":
            fails += 1
        elif r["status"] == "warn":
            warns += 1
    status = "fail" if fails else ("warn" if warns else "pass")
    return {"status": status, "fails": fails, "warns": warns, "gates": gates}


def annotate(catalog: dict, mapping: dict, reports: dict[str, dict]) -> dict:
    out = copy.deepcopy(catalog)
    # Anatomy's real catalog format keys nodes by id ({id: node}); the early
    # sample used a list of {id, ...}. Accept both.
    raw_nodes = out.get("nodes") or {}
    if isinstance(raw_nodes, dict):
        nodes = raw_nodes
    else:
        nodes = {n["id"]: n for n in raw_nodes if isinstance(n, dict) and "id" in n}
    as_of = datetime.now(timezone.utc).isoformat(timespec="seconds")

    failing_nodes: list[str] = []
    applied, unmapped_sources, unknown_nodes = 0, [], []

    for source, node_ids in (mapping.get("map") or {}).items():
        if source not in reports:
            unmapped_sources.append(source)
            continue
        verdict = summarize(reports[source])
        verdict["source"] = source
        verdict["asOf"] = as_of
        for node_id in node_ids if isinstance(node_ids, list) else [node_ids]:
            node = nodes.get(node_id)
            if node is None:
                unknown_nodes.append(node_id)
                continue
            node["gov"] = verdict
            applied += 1
            if verdict["status"] == "fail":
                failing_nodes.append(node_id)

    meta = out.setdefault("meta", {})
    meta["governance"] = {
        "generatedBy": "plumbline_to_anatomy",
        "asOf": as_of,
        "sources": sorted(reports),
        "annotated": applied,
        "failing": sorted(failing_nodes),
    }
    # Zero-renderer-change visibility: failing systems become a scope ring.
    scopes = meta.setdefault("scopes", [])
    scopes[:] = [s for s in scopes if s.get("id") != "GOV"]
    if failing_nodes:
        scopes.append(GOV_RING)
        for node_id in failing_nodes:
            node_scopes = nodes[node_id].setdefault("scopes", [])
            if "GOV" not in node_scopes:
                node_scopes.append("GOV")

    if unmapped_sources:
        print(f"note: mapping references reports not provided: {unmapped_sources}")
    if unknown_nodes:
        print(f"note: mapping references node ids not in catalog: {unknown_nodes}")
    return out


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--catalog", required=True)
    ap.add_argument("--mapping", required=True)
    ap.add_argument("--report", action="append", required=True,
                    help="source_name:path/to/report.json (repeatable)")
    ap.add_argument("--out", required=True)
    args = ap.parse_args()

    catalog = json.loads(Path(args.catalog).read_text(encoding="utf-8"))
    mapping = yaml.safe_load(Path(args.mapping).read_text(encoding="utf-8")) or {}
    reports = load_reports(args.report)

    annotated = annotate(catalog, mapping, reports)
    Path(args.out).write_text(
        json.dumps(annotated, indent=2, ensure_ascii=False) + "\n", encoding="utf-8"
    )
    gov = annotated["meta"]["governance"]
    print(f"annotated {gov['annotated']} node(s); failing: {gov['failing'] or 'none'}")
    print(f"wrote {args.out}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
