# Roadmap

## v0.2 (shipped)
- SHA-pinned all GitHub Actions (supply-chain hardening, zizmor-verified).
- Added `iac_scan` gate (checkov-based; Terraform / Bicep / CloudFormation).
- Added `foundry_iac` profile: `[project_pack, secrets, actions_security, deps_audit, iac_scan]`.
- Added `.github/copilot-instructions.md` (Copilot equivalent of CLAUDE.md/AGENTS.md).

## Now
Validate on CloudIntelMatrix: schema_check against capability.schema.json, data_freshness on PQC/FedRAMP records.

## Next
Gate: repo settings audit via GitHub API (branch protection, CODEOWNERS). Semgrep ruleset. SARIF output for the GitHub Security tab.

## Later
LLM layer on, Batch API nightly sweep, multi-repo orchestration.

## Explicitly not building yet
Dashboards, auto-fix PRs. One repo proves it first.
