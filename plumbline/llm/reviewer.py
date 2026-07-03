"""Tiered LLM review layer. OFF by default; deterministic gates never call this."""

from __future__ import annotations

import hashlib
import json
import os
import subprocess
from pathlib import Path

from plumbline.config import Config

PROMPT_VERSION = "1"

SYSTEM_PROMPT = """You are Plumbline, a skeptical principal-architect reviewer.
You receive ONE file from a repository. Review it for:
- security flaws
- prompt-injection exposure if the file builds prompts or handles untrusted content
- architectural smells
- misleading naming or docs that overstate what the code does
Do not flatter. Do not restate the code. Report only material findings.
Respond ONLY with JSON, no markdown fences:
{"findings":[{"severity":"low|medium|high|critical","message":"...","line":0}],
 "escalate": false, "summary": "one sentence"}
Set "escalate": true only if a finding is high/critical and uncertain enough that a stronger model should confirm before a human is alerted."""


def _changed_files(root: Path, base_ref: str) -> list[Path]:
    try:
        out = subprocess.run(
            ["git", "diff", "--name-only", "--diff-filter=ACM", base_ref, "HEAD"],
            cwd=root, capture_output=True, text=True, timeout=60, check=True)
    except subprocess.SubprocessError:
        return []
    exts = {".py", ".js", ".ts", ".go", ".yaml", ".yml", ".json", ".md", ".sh", ".bicep", ".tf"}
    files = []
    for line in out.stdout.splitlines():
        p = root / line.strip()
        if p.exists() and p.suffix in exts and p.stat().st_size < 200_000:
            files.append(p)
    return files


def _cache_key(content: str) -> str:
    return hashlib.sha256(f"v{PROMPT_VERSION}\n{content}".encode()).hexdigest()


def review_changes(root: Path, cfg: Config, base_ref: str = "origin/main") -> dict:
    if not cfg.llm.enabled:
        return {"reviewed": 0, "cached": 0, "findings": [], "cost_note": "llm layer disabled"}
    if not os.environ.get("ANTHROPIC_API_KEY"):
        return {"reviewed": 0, "cached": 0, "findings": [], "cost_note": "ANTHROPIC_API_KEY not set; llm layer skipped"}
    try:
        import anthropic
    except ImportError:
        return {"reviewed": 0, "cached": 0, "findings": [], "cost_note": "anthropic package not installed; llm layer skipped"}

    client = anthropic.Anthropic()
    cache_dir = root / cfg.llm.cache_dir
    cache_dir.mkdir(parents=True, exist_ok=True)

    files = _changed_files(root, base_ref)[: cfg.llm.max_files_per_run]
    all_findings, reviewed, cached = [], 0, 0

    for f in files:
        content = f.read_text(errors="replace")
        key = _cache_key(content)
        cache_file = cache_dir / f"{key}.json"
        if cache_file.exists():
            cached += 1
            result = json.loads(cache_file.read_text())
        else:
            result = _call(client, cfg.llm.default_model, content, f.name)
            if result.get("escalate"):
                result = _call(client, cfg.llm.escalation_model, content, f.name)
                result["escalated"] = True
            cache_file.write_text(json.dumps(result))
            reviewed += 1
        for finding in result.get("findings", []):
            finding["file"] = str(f.relative_to(root))
            all_findings.append(finding)

    return {"reviewed": reviewed, "cached": cached, "findings": all_findings,
            "cost_note": f"{reviewed} API reviews, {cached} cache hits, {len(files)} files in scope (cap {cfg.llm.max_files_per_run})"}


def _call(client, model: str, content: str, filename: str) -> dict:
    resp = client.messages.create(
        model=model,
        max_tokens=1500,
        system=[{"type": "text", "text": SYSTEM_PROMPT, "cache_control": {"type": "ephemeral"}}],
        messages=[{"role": "user", "content": f"File: {filename}\n\n{content}"}],
    )
    text = "".join(b.text for b in resp.content if getattr(b, "type", "") == "text")
    text = text.replace("```json", "").replace("```", "").strip()
    try:
        return json.loads(text)
    except json.JSONDecodeError:
        return {"findings": [{"severity": "low", "message": "reviewer returned unparseable output", "line": 0}], "escalate": False, "summary": "parse error"}
