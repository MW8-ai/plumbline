"""Built-in deterministic gates."""

from __future__ import annotations

import json
import subprocess
import tempfile
import time
from pathlib import Path

from plumbline.config import Config
from plumbline.gates.base import Finding, GateResult, Status, register, run_tool, skip, tool_available

PACK_FILES = ["README.md", "SECURITY.md", "docs/THREAT_MODEL.md", "docs/DECISIONS.md", "docs/ROADMAP.md", "LICENSE"]
AI_PACK_FILES = ["docs/AI_GUARDRAILS.md", "docs/EVALS.md"]
MIN_BYTES = 120


def _check_files(root: Path, files: list[str], gate: str) -> GateResult:
    findings: list[Finding] = []
    for rel in files:
        p = root / rel
        if not p.exists():
            findings.append(Finding(f"missing required file: {rel}", rel, "high"))
        elif p.stat().st_size < MIN_BYTES:
            findings.append(Finding(f"file exists but is near-empty: {rel}", rel, "medium"))
    status = Status.FAIL if any(f.severity == "high" for f in findings) else (Status.WARN if findings else Status.PASS)
    return GateResult(gate=gate, status=status, findings=findings)


@register("project_pack")
def project_pack(root: Path, cfg: Config) -> GateResult:
    files = cfg.required_files if cfg.required_files is not None else PACK_FILES
    return _check_files(root, files, "project_pack")


@register("ai_pack")
def ai_pack(root: Path, cfg: Config) -> GateResult:
    return _check_files(root, AI_PACK_FILES, "ai_pack")


@register("secrets")
def secrets(root: Path, cfg: Config) -> GateResult:
    if not tool_available("gitleaks"):
        return skip("secrets", "gitleaks", "install gitleaks or use the CI workflow")
    with tempfile.TemporaryDirectory() as tmp_dir:
        report_path = Path(tmp_dir) / "gitleaks-report.json"
        proc = run_tool(["gitleaks", "detect", "--no-banner", "--report-format", "json", "--report-path", str(report_path), "--exit-code", "2"], root)
        if proc.returncode == 0:
            return GateResult("secrets", Status.PASS)
        findings = []
        try:
            report_text = report_path.read_text(encoding="utf-8") if report_path.exists() else "[]"
            for item in json.loads(report_text or "[]"):
                findings.append(Finding(f"potential secret: {item.get('RuleID', 'unknown rule')}", f"{item.get('File', '?')}:{item.get('StartLine', '?')}", "critical"))
        except json.JSONDecodeError:
            findings.append(Finding("secret scanner reported findings", "", "critical"))
    return GateResult("secrets", Status.FAIL, findings)


@register("actions_security")
def actions_security(root: Path, cfg: Config) -> GateResult:
    wf_dir = root / ".github" / "workflows"
    if not wf_dir.exists():
        return GateResult("actions_security", Status.PASS, detail="no workflows directory")
    if not tool_available("zizmor"):
        return skip("actions_security", "zizmor", "pip install zizmor")
    proc = run_tool(["zizmor", "--format", "json", str(wf_dir)], root)
    findings = []
    try:
        for item in json.loads(proc.stdout or "[]"):
            ident = item.get("ident", "finding")
            sev = (item.get("determinations", {}) or {}).get("severity", "medium")
            findings.append(Finding(f"zizmor:{ident}", "workflows", str(sev).lower()))
    except json.JSONDecodeError:
        if proc.returncode != 0:
            findings.append(Finding("zizmor findings", "workflows", "medium"))
    high = any(f.severity in ("high", "critical") for f in findings)
    return GateResult("actions_security", Status.FAIL if high else (Status.WARN if findings else Status.PASS), findings)


@register("deps_audit")
def deps_audit(root: Path, cfg: Config) -> GateResult:
    findings: list[Finding] = []
    ran = False
    if any((root / m).exists() for m in ("pyproject.toml", "requirements.txt")) and tool_available("pip-audit"):
        ran = True
        proc = run_tool(["pip-audit", "--format", "json", "--progress-spinner", "off"], root)
        try:
            data = json.loads(proc.stdout or "{}")
            for dep in data.get("dependencies", []):
                for v in dep.get("vulns", []):
                    findings.append(Finding(f"{dep.get('name')}=={dep.get('version')}: {v.get('id')}", "python deps", "high"))
        except json.JSONDecodeError:
            pass
    if (root / "package.json").exists() and tool_available("npm"):
        ran = True
        proc = run_tool(["npm", "audit", "--json", "--audit-level=high"], root)
        try:
            meta = json.loads(proc.stdout or "{}").get("metadata", {})
            counts = meta.get("vulnerabilities", {})
            n = int(counts.get("high", 0)) + int(counts.get("critical", 0))
            if n:
                findings.append(Finding(f"{n} high/critical npm vulnerabilities", "node deps", "high"))
        except (json.JSONDecodeError, subprocess.SubprocessError):
            pass
    if not ran:
        return GateResult("deps_audit", Status.SKIP, detail="no manifests found or audit tools unavailable")
    return GateResult("deps_audit", Status.FAIL if findings else Status.PASS, findings)


@register("lint")
def lint(root: Path, cfg: Config) -> GateResult:
    if not any(root.rglob("*.py")):
        return GateResult("lint", Status.PASS, detail="no Python files")
    if not tool_available("ruff"):
        return skip("lint", "ruff", "pip install ruff")
    proc = run_tool(["ruff", "check", "--output-format", "json", "."], root)
    findings = []
    try:
        for item in json.loads(proc.stdout or "[]"):
            findings.append(Finding(f"{item.get('code')}: {item.get('message')}", f"{item.get('filename')}:{(item.get('location') or {}).get('row', '?')}", "low"))
    except json.JSONDecodeError:
        pass
    return GateResult("lint", Status.WARN if findings else Status.PASS, findings)


@register("tests_present")
def tests_present(root: Path, cfg: Config) -> GateResult:
    hits = list(root.glob("tests/**/test_*.py")) + list(root.glob("**/*_test.go")) + list(root.glob("tests/**/*.test.*"))
    if hits:
        return GateResult("tests_present", Status.PASS, detail=f"{len(hits)} test files")
    return GateResult("tests_present", Status.FAIL, [Finding("no test files found under tests/", "tests/", "high")])


@register("schema_check")
def schema_check(root: Path, cfg: Config) -> GateResult:
    if not cfg.schema_pairs:
        return GateResult("schema_check", Status.SKIP, detail="no schema_pairs configured")
    try:
        import jsonschema
    except ImportError:
        return skip("schema_check", "jsonschema", "pip install jsonschema")
    findings: list[Finding] = []
    for pair in cfg.schema_pairs:
        schema_path = root / pair["schema"]
        if not schema_path.exists():
            findings.append(Finding(f"schema not found: {pair['schema']}", pair["schema"], "high"))
            continue
        schema = json.loads(schema_path.read_text())
        validator = jsonschema.Draft202012Validator(schema)
        for data_file in sorted(root.glob(pair["data"])):
            try:
                doc = json.loads(data_file.read_text())
            except json.JSONDecodeError as e:
                findings.append(Finding(f"invalid JSON: {e}", str(data_file), "high"))
                continue
            for err in validator.iter_errors(doc):
                path = "/".join(str(p) for p in err.absolute_path) or "(root)"
                findings.append(Finding(err.message[:200], f"{data_file}:{path}", "high"))
    return GateResult("schema_check", Status.FAIL if findings else Status.PASS, findings)


@register("data_freshness")
def data_freshness(root: Path, cfg: Config) -> GateResult:
    if not cfg.data_freshness_paths:
        return GateResult("data_freshness", Status.SKIP, detail="no data_freshness_paths configured")
    cutoff = time.time() - cfg.data_freshness_days * 86400
    findings = []
    for pattern in cfg.data_freshness_paths:
        for f in sorted(root.glob(pattern)):
            ts = None
            try:
                out = subprocess.run(["git", "log", "-1", "--format=%ct", "--", str(f.relative_to(root))], cwd=root, capture_output=True, text=True, timeout=30)
                if out.stdout.strip():
                    ts = int(out.stdout.strip())
            except (subprocess.SubprocessError, ValueError):
                pass
            if ts is None:
                ts = f.stat().st_mtime
            if ts < cutoff:
                days = int((time.time() - ts) / 86400)
                findings.append(Finding(f"data file last updated {days} days ago (threshold {cfg.data_freshness_days})", str(f.relative_to(root)), "medium"))
    return GateResult("data_freshness", Status.WARN if findings else Status.PASS, findings)
