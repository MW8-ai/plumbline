"""IaC security gate powered by checkov."""

from __future__ import annotations

import json
from pathlib import Path

from plumbline.config import Config
from plumbline.gates.base import Finding, GateResult, Status, register, run_tool, skip, tool_available


@register("iac_scan")
def iac_scan(root: Path, cfg: Config) -> GateResult:
    """Run checkov against any Terraform / Bicep / CloudFormation files in the repo.

    - SKIP politely if checkov is not installed.
    - FAIL on any HIGH-severity finding.
    - WARN on lower-severity findings.
    - PASS when no IaC files are present or checkov reports clean.
    """
    if not tool_available("checkov"):
        return skip("iac_scan", "checkov", "pip install checkov")

    tf_files = list(root.rglob("*.tf"))
    bicep_files = list(root.rglob("*.bicep"))
    cf_files = list(root.rglob("*.template.json")) + list(root.rglob("template.yaml"))

    if not (tf_files or bicep_files or cf_files):
        return GateResult("iac_scan", Status.PASS, detail="no IaC files found")

    proc = run_tool(
        [
            "checkov",
            "--directory", str(root),
            "--output", "json",
            "--quiet",
            "--compact",
        ],
        root,
    )

    findings: list[Finding] = []
    try:
        raw = proc.stdout or "{}"
        # checkov may emit multiple JSON objects for different frameworks; take the last valid one
        data: dict = {}
        for line in raw.splitlines():
            line = line.strip()
            if line.startswith("{"):
                try:
                    data = json.loads(line)
                except json.JSONDecodeError:
                    pass
        if not data and raw.strip().startswith("{"):
            data = json.loads(raw)

        failed_checks = data.get("results", {}).get("failed_checks", [])
        for check in failed_checks:
            sev = str(check.get("severity") or "medium").lower()
            check_id = check.get("check_id", "unknown")
            check_type = check.get("check_type", "")
            resource = check.get("resource", "")
            file_path = check.get("file_path", "")
            location = f"{file_path}:{resource}" if resource else file_path
            findings.append(Finding(
                message=f"{check_id} ({check_type}): {check.get('check', check_id)}",
                location=location,
                severity="high" if sev in ("high", "critical") else "medium",
            ))
    except (json.JSONDecodeError, AttributeError):
        if proc.returncode not in (0, 1):
            findings.append(Finding("checkov failed to run", str(root), "medium"))

    high = any(f.severity in ("high", "critical") for f in findings)
    status = Status.FAIL if high else (Status.WARN if findings else Status.PASS)
    return GateResult("iac_scan", status, findings)
