"""Plumbline CLI."""

from __future__ import annotations

import argparse
import json
import shutil
import sys
from pathlib import Path

from plumbline import config as cfg_mod
from plumbline.gates import builtin  # noqa: F401
from plumbline.gates import iac_gates  # noqa: F401
from plumbline.gates.base import Status, registry

TEMPLATES = Path(__file__).parent / "templates"


def run_check(root: Path, use_llm: bool, base_ref: str) -> int:
    cfg = cfg_mod.load(root)
    results = []
    for name in cfg.resolved_gates():
        fn = registry().get(name)
        if fn is None:
            print(f"unknown gate: {name}")
            continue
        results.append(fn(root, cfg))

    llm_report = None
    if use_llm:
        from plumbline.llm.reviewer import review_changes
        llm_report = review_changes(root, cfg, base_ref)

    out_dir = root / ".plumbline"
    out_dir.mkdir(exist_ok=True)
    payload = {
        "profile": cfg.project_type,
        "results": [
            {"gate": r.gate, "status": r.status.value, "detail": r.detail,
             "findings": [vars(f) for f in r.findings]}
            for r in results
        ],
        "llm": llm_report,
    }
    (out_dir / "report.json").write_text(json.dumps(payload, indent=2))
    lines = [f"# Plumbline report — profile `{cfg.project_type}`", ""]
    failed = False
    for r in results:
        lines.append(f"## {r.gate} — **{r.status.value.upper()}**")
        if r.detail:
            lines.append(r.detail)
        for f in r.findings:
            loc = f" — `{f.location}`" if f.location else ""
            lines.append(f"- **{f.severity}**: {f.message}{loc}")
        lines.append("")
        failed = failed or r.blocking
    if llm_report is not None:
        lines.append(f"## llm_review\n{llm_report['cost_note']}")
        for f in llm_report["findings"]:
            lines.append(f"- **{f.get('severity')}**: {f.get('message')} — `{f.get('file')}`")
    (out_dir / "report.md").write_text("\n".join(lines))

    icon = {Status.PASS: "PASS", Status.WARN: "WARN", Status.FAIL: "FAIL", Status.SKIP: "SKIP"}
    print(f"\nPlumbline — profile '{cfg.project_type}' — {len(results)} gates\n")
    for r in results:
        print(f"  [{icon[r.status]}] {r.gate}" + (f" — {r.detail}" if r.detail else ""))
    print(f"\nReports: {out_dir / 'report.md'}\n")
    return 1 if failed else 0


def run_init(root: Path) -> int:
    created = []
    for item in sorted(TEMPLATES.rglob("*")):
        if item.is_dir():
            continue
        rel = item.relative_to(TEMPLATES)
        dest = root / rel
        if dest.exists():
            continue
        dest.parent.mkdir(parents=True, exist_ok=True)
        shutil.copy2(item, dest)
        created.append(str(rel))
    print("Created:" if created else "Nothing to create; all files already exist.")
    for c in created:
        print(f"  + {c}")
    return 0


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(prog="plumbline")
    sub = parser.add_subparsers(dest="cmd")
    p_check = sub.add_parser("check", help="run gates")
    p_check.add_argument("path", nargs="?", default=".")
    p_check.add_argument("--llm", action="store_true")
    p_check.add_argument("--base-ref", default="origin/main")
    p_init = sub.add_parser("init", help="drop config and governance templates")
    p_init.add_argument("path", nargs="?", default=".")
    sub.add_parser("gates", help="list gates and profiles")

    args = parser.parse_args(argv)
    if args.cmd == "check":
        return run_check(Path(args.path).resolve(), args.llm, args.base_ref)
    if args.cmd == "init":
        return run_init(Path(args.path).resolve())
    if args.cmd == "gates":
        print("Gates:", ", ".join(sorted(registry())))
        for name, gates in cfg_mod.PROFILES.items():
            print(f"  {name}: {', '.join(gates)}")
        return 0
    parser.print_help()
    return 2


if __name__ == "__main__":
    sys.exit(main())
