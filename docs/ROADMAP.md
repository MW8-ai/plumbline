# Roadmap

## v0.2 (complete)
- SHA-pinned all GitHub Actions in `.github/workflows/*.yml` (supply-chain hardening).
- Added `iac_scan` gate: checkov-based IaC scan, FAILs on high-severity findings, WARNs otherwise, skips politely when checkov is absent.
- Added `foundry_iac` profile: `[project_pack, secrets, actions_security, deps_audit, iac_scan]`.

## Now
Validate on CloudIntelMatrix: schema_check against capability.schema.json, data_freshness on PQC/FedRAMP records.

## Next
Gate: repo settings audit via GitHub API (branch protection, CODEOWNERS). Semgrep ruleset.

## Later
LLM layer on, Batch API nightly sweep, SARIF output for the GitHub Security tab.

## Explicitly not building yet
Dashboards, multi-repo orchestration, auto-fix PRs. One repo proves it first.
