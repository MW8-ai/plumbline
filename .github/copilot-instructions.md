# GitHub Copilot Instructions for plumbline

## Before finishing any task

Run the plumbline self-check on this repository:

```bash
pip install -e ".[scanners,dev]"
plumbline check .
```

The check must exit **0** (no FAILs). If a gate finding is a genuine false
positive, document it in the PR description — **do not weaken or skip the gate
to make the check pass**.

## Gate rules

- **Never weaken a gate** to make a check pass.
- **Never raise the severity threshold** of an existing gate to silence findings.
- If a scanner finding is a false positive, document it in the PR with a clear
  justification (tool name, rule ID, reason it does not apply here).
- New gates must follow the pattern in `plumbline/gates/builtin.py`:
  `SKIP` politely when the required tool is absent, `FAIL` on high-severity
  findings, `WARN` otherwise.

## Code style

- Run `ruff check .` before committing; fix all findings.
- All new gates must be covered by at least one test in `tests/test_gates.py`.
- Import new gate modules in `plumbline/cli.py` next to the existing imports so
  they are registered at startup.

## Commits

- Commit in small, logical units (one concern per commit).
- Prefix with a conventional-commit type: `feat:`, `fix:`, `chore:`, `docs:`.
- Do not squash or force-push to branches under active review.
