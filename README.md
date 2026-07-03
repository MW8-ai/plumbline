# Plumbline

Deterministic-first project governance harness. The enforcement arm of
[Architect's Cornerstone](https://github.com/MW8-ai): Cornerstone defines the
standard, Plumbline verifies the build is true.

A plumb line has no opinions and no API bill. Plumbline runs free, boring,
best-in-class scanners first, and spends LLM tokens only on the judgment calls
those tools cannot make — reviewing changed files only, caching every verdict,
and escalating models only when needed.

## Why

Auditing every repo with a frontier model is expensive and mostly wasteful:
roughly 70% of a governance audit (secrets, workflow injection, dependency
CVEs, missing docs, schema drift) is deterministic. Plumbline encodes that
split:

| Layer | Cost | What it does |
|-------|------|--------------|
| Gates | $0 | gitleaks, zizmor, pip-audit, ruff, jsonschema, file-pack + freshness checks |
| Policy | $0 | `plumbline.yaml` per repo, profiles per project type |
| LLM review | opt-in | diff-only, hash-cached, Haiku-first with Sonnet escalation |

## Quickstart

```bash
pip install "plumbline[scanners] @ git+https://github.com/MW8-ai/plumbline@main"
cd your-repo
plumbline init      # drops plumbline.yaml + governance doc pack
plumbline check     # runs the gates, writes .plumbline/report.md
```

CI (any repo, one file):

```yaml
# .github/workflows/governance.yml
name: governance
on: [push, pull_request]
permissions: { contents: read }
jobs:
  plumbline:
    uses: MW8-ai/plumbline/.github/workflows/plumbline.yml@main
    with: { llm_review: false }
```

## Profiles

`default`, `api`, `reference_data` (schema validation + data freshness for
accuracy-critical repos like CloudIntelMatrix), `agent` and `skill` (adds the
AI guardrails/evals doc pack). See `plumbline gates`.

## LLM layer cost model

- Reviews only files changed vs the base ref, hard-capped per run.
- Verdicts cached by content hash — an unchanged file never costs twice.
- `claude-haiku-4-5` ($1/$5 per MTok) reviews; `claude-sonnet-4-6` confirms
  only findings Haiku marks for escalation.
- Stable system prompt uses prompt caching (90% off cache reads).
- Nightly full sweeps, if you want them, belong on the Batch API (50% off).

## Design rules

Small PRs. Pinned actions. Least-privilege tokens. Human approval before
anything risky. No auto-merge, ever — the self-update workflow opens an
issue and a human decides. Boring on purpose.

## License

MIT
