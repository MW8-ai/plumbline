"""Gate framework: every check is a Gate returning a GateResult.

Design rules:
- Gates are deterministic and cheap. No LLM calls in gates, ever.
- External scanners (gitleaks, zizmor, pip-audit, ruff) are invoked if
  installed; if missing, the gate reports SKIPPED with install guidance
  rather than failing the run. CI installs them; local runs degrade politely.
- Exit semantics: FAIL blocks, WARN reports, PASS/SKIP do not block.
"""

from __future__ import annotations

import dataclasses
import shutil
import subprocess
from enum import Enum
from pathlib import Path
from typing import Callable

from plumbline.config import Config


class Status(str, Enum):
    PASS = "pass"
    WARN = "warn"
    FAIL = "fail"
    SKIP = "skip"


@dataclasses.dataclass
class Finding:
    message: str
    location: str = ""
    severity: str = "medium"  # low | medium | high | critical


@dataclasses.dataclass
class GateResult:
    gate: str
    status: Status
    findings: list[Finding] = dataclasses.field(default_factory=list)
    detail: str = ""

    @property
    def blocking(self) -> bool:
        return self.status == Status.FAIL


GateFn = Callable[[Path, Config], GateResult]
_REGISTRY: dict[str, GateFn] = {}


def register(name: str) -> Callable[[GateFn], GateFn]:
    def deco(fn: GateFn) -> GateFn:
        _REGISTRY[name] = fn
        return fn

    return deco


def registry() -> dict[str, GateFn]:
    return dict(_REGISTRY)


def tool_available(name: str) -> bool:
    return shutil.which(name) is not None


def run_tool(cmd: list[str], cwd: Path) -> subprocess.CompletedProcess:
    return subprocess.run(cmd, cwd=cwd, capture_output=True, text=True, timeout=600)


def skip(gate: str, tool: str, install_hint: str) -> GateResult:
    return GateResult(
        gate=gate,
        status=Status.SKIP,
        detail=f"'{tool}' not installed; skipped. Install: {install_hint}",
    )
