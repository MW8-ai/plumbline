# Threat Model

## Assets
What must be protected (data accuracy, credentials, published artifacts, user trust).

## Actors
Maintainer, contributors, CI, external consumers, attackers (supply chain, workflow injection, prompt injection if AI is involved).

## Entry points
PRs, issues, dependencies, GitHub Actions, external data sources, user input.

## Key risks and mitigations
Risk | Likelihood | Impact | Mitigation
--- | --- | --- | ---
Workflow injection via untrusted PR input | | | pinned actions, least-privilege token, no pull_request_target with checkout
Dependency compromise | | | pip-audit/Dependabot, lockfiles
Secret leakage | | | gitleaks gate, no long-lived cloud keys
