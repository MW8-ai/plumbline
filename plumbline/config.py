"""Plumbline configuration: loads plumbline.yaml and resolves the gate profile."""

from __future__ import annotations

import dataclasses
from pathlib import Path
from typing import Any

import yaml

PROFILES: dict[str, list[str]] = {
    "default": ["project_pack", "secrets", "actions_security", "deps_audit", "lint"],
    "api": ["project_pack", "secrets", "actions_security", "deps_audit", "lint", "tests_present"],
    "reference_data": [
        "project_pack",
        "secrets",
        "actions_security",
        "deps_audit",
        "lint",
        "schema_check",
        "data_freshness",
    ],
    "agent": [
        "project_pack",
        "ai_pack",
        "secrets",
        "actions_security",
        "deps_audit",
        "lint",
        "tests_present",
    ],
    "skill": ["project_pack", "ai_pack", "secrets", "lint"],
}


@dataclasses.dataclass
class LLMConfig:
    enabled: bool = False
    default_model: str = "claude-haiku-4-5"
    escalation_model: str = "claude-sonnet-4-6"
    max_files_per_run: int = 20
    cache_dir: str = ".plumbline/cache"


@dataclasses.dataclass
class Config:
    project_type: str = "default"
    gates: list[str] = dataclasses.field(default_factory=list)
    add_gates: list[str] = dataclasses.field(default_factory=list)
    skip_gates: list[str] = dataclasses.field(default_factory=list)
    required_files: list[str] | None = None
    schema_pairs: list[dict[str, str]] = dataclasses.field(default_factory=list)
    data_freshness_days: int = 90
    data_freshness_paths: list[str] = dataclasses.field(default_factory=list)
    llm: LLMConfig = dataclasses.field(default_factory=LLMConfig)
    raw: dict[str, Any] = dataclasses.field(default_factory=dict)

    def resolved_gates(self) -> list[str]:
        base = list(self.gates) if self.gates else list(
            PROFILES.get(self.project_type, PROFILES["default"])
        )
        for g in self.add_gates:
            if g not in base:
                base.append(g)
        return [g for g in base if g not in self.skip_gates]


def load(repo_root: Path) -> Config:
    path = repo_root / "plumbline.yaml"
    if not path.exists():
        return Config()
    data = yaml.safe_load(path.read_text()) or {}
    llm_raw = data.get("llm", {}) or {}
    return Config(
        project_type=data.get("project_type", "default"),
        gates=data.get("gates", []) or [],
        add_gates=data.get("add_gates", []) or [],
        skip_gates=data.get("skip_gates", []) or [],
        required_files=data.get("required_files"),
        schema_pairs=data.get("schema_pairs", []) or [],
        data_freshness_days=int(data.get("data_freshness_days", 90)),
        data_freshness_paths=data.get("data_freshness_paths", []) or [],
        llm=LLMConfig(
            enabled=bool(llm_raw.get("enabled", False)),
            default_model=llm_raw.get("default_model", "claude-haiku-4-5"),
            escalation_model=llm_raw.get("escalation_model", "claude-sonnet-4-6"),
            max_files_per_run=int(llm_raw.get("max_files_per_run", 20)),
            cache_dir=llm_raw.get("cache_dir", ".plumbline/cache"),
        ),
        raw=data,
    )
