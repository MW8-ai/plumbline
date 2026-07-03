"""IaC (Infrastructure-as-Code) gate — checkov-based scan."""

from __future__ import annotations

import json
from pathlib import Path

from plumbline.config import Config
from plumbline.gates.base import Finding, GateResult, Status, register, run_tool, skip, tool_available


@register("iac_scan")
def iac_scan(root: Path, cfg: Config) -> GateResult:
    tf_files = list(root.rglob("*.tf")) + list(root.rglob("*.bicep"))
    if not tf_files:
        return GateResult("iac_scan", Status.PASS, detail="no IaC files found (.tf, .bicep)")
    if not tool_available("checkov"):
        return skip("iac_scan", "checkov", "pip install checkov")
    proc = run_tool(
        ["checkov", "--directory", str(root), "--output", "json", "--quiet"],
        root,
    )
    findings: list[Finding] = []
    try:
        data = json.loads(proc.stdout or "{}")
        results = data if isinstance(data, list) else [data]
        for block in results:
            for check in block.get("results", {}).get("failed_checks", []):
                severity = str(check.get("severity") or "medium").lower()
                check_id = check.get("check_id", "unknown")
                check_type = check.get("check_type", "")
                resource = check.get("resource", "")
                file_path = check.get("repo_file_path") or check.get("file_path") or ""
                line = check.get("file_line_range", [None])[0]
                loc = f"{file_path}:{line}" if line else file_path
                findings.append(Finding(
                    f"{check_id} ({check_type}): {resource}",
                    loc,
                    "high" if severity in ("high", "critical") else "medium",
                ))
    except (json.JSONDecodeError, KeyError, TypeError):
        if proc.returncode not in (0, 1):
            findings.append(Finding("checkov produced unexpected output", "", "medium"))

    high = any(f.severity in ("high", "critical") for f in findings)
    if high:
        return GateResult("iac_scan", Status.FAIL, findings)
    if findings:
        return GateResult("iac_scan", Status.WARN, findings)
    return GateResult("iac_scan", Status.PASS)
