import json
from pathlib import Path

from plumbline import config as cfg_mod
from plumbline.gates import builtin  # noqa: F401
from plumbline.gates.base import Status, registry
from plumbline.cli import run_check, run_init


def make_repo(tmp_path: Path) -> Path:
    (tmp_path / "docs").mkdir()
    for f in ["README.md", "SECURITY.md", "LICENSE"]:
        (tmp_path / f).write_text("x" * 200)
    for f in ["docs/THREAT_MODEL.md", "docs/DECISIONS.md", "docs/ROADMAP.md"]:
        (tmp_path / f).write_text("x" * 200)
    return tmp_path


def test_project_pack_pass(tmp_path):
    repo = make_repo(tmp_path)
    r = registry()["project_pack"](repo, cfg_mod.Config())
    assert r.status == Status.PASS


def test_project_pack_fail_on_missing(tmp_path):
    r = registry()["project_pack"](tmp_path, cfg_mod.Config())
    assert r.status == Status.FAIL
    assert any("README.md" in f.message for f in r.findings)


def test_near_empty_file_warns(tmp_path):
    repo = make_repo(tmp_path)
    (repo / "SECURITY.md").write_text("todo")
    r = registry()["project_pack"](repo, cfg_mod.Config())
    assert r.status == Status.WARN


def test_schema_check_catches_invalid(tmp_path):
    (tmp_path / "schema").mkdir(); (tmp_path / "data").mkdir()
    (tmp_path / "schema" / "s.json").write_text(json.dumps({
        "type": "object", "required": ["name"],
        "properties": {"name": {"type": "string"}}}))
    (tmp_path / "data" / "good.json").write_text(json.dumps({"name": "aws"}))
    (tmp_path / "data" / "bad.json").write_text(json.dumps({"nope": 1}))
    cfg = cfg_mod.Config(schema_pairs=[{"schema": "schema/s.json", "data": "data/*.json"}])
    r = registry()["schema_check"](tmp_path, cfg)
    assert r.status == Status.FAIL
    assert any("bad.json" in f.location for f in r.findings)


def test_profile_resolution():
    cfg = cfg_mod.Config(project_type="reference_data", skip_gates=["lint"], add_gates=["tests_present"])
    gates = cfg.resolved_gates()
    assert "schema_check" in gates and "lint" not in gates and "tests_present" in gates


def test_tests_present_gate(tmp_path):
    r = registry()["tests_present"](tmp_path, cfg_mod.Config())
    assert r.status == Status.FAIL
    (tmp_path / "tests").mkdir()
    (tmp_path / "tests" / "test_x.py").write_text("def test_x(): pass")
    r2 = registry()["tests_present"](tmp_path, cfg_mod.Config())
    assert r2.status == Status.PASS


def test_init_then_check_roundtrip(tmp_path):
    run_init(tmp_path)
    assert (tmp_path / "plumbline.yaml").exists()
    assert (tmp_path / "docs" / "AI_GUARDRAILS.md").exists()
    (tmp_path / "README.md").write_text("x" * 200)
    (tmp_path / "LICENSE").write_text("x" * 200)
    code = run_check(tmp_path, use_llm=False, base_ref="origin/main")
    assert code in (0, 1)
    assert (tmp_path / ".plumbline" / "report.json").exists()


def test_llm_disabled_is_free(tmp_path):
    from plumbline.llm.reviewer import review_changes
    out = review_changes(tmp_path, cfg_mod.Config())
    assert out["reviewed"] == 0 and "disabled" in out["cost_note"]
