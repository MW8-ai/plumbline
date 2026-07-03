# Security Policy

## Reporting a vulnerability
Open a private security advisory on this repository or contact the maintainer directly. Do not open public issues for vulnerabilities.

## Scope
Describe what is in scope (code, workflows, published artifacts) and out of scope.

## Secrets
No credentials are stored in this repository. CI uses OIDC/short-lived tokens where cloud access is required. GITHUB_TOKEN runs with least-privilege permissions declared per workflow.
