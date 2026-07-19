# Decision Log

| Date | Decision | Alternatives considered | Why |
|------|----------|------------------------|-----|
| 2026-07-03 | SHA-pin all GitHub Actions | Keep floating version tags | Floating tags are mutable; pinning to a commit SHA prevents supply-chain attacks where a tag is silently moved to malicious code. Version kept as trailing comment for readability. |
| 2026-07-03 | Add `iac_scan` gate (checkov-based) | Integrate Terraform linting via tflint | checkov covers multiple IaC formats (Terraform, Bicep) and maps findings to severity levels we already use. Skips politely when checkov is not installed. |
| 2026-07-03 | Add `foundry_iac` profile | Extend `default` profile | IaC repos have distinct concerns; a dedicated profile avoids bloating the default and makes the intent explicit. |
| 2026-07-18 | Bump gitleaks pin in `plumbline.yml` from v8.21.2 to v8.30.1 | Leave stale | Closes recurring self-update staleness issues (#6, #17); the download is a curl'd release binary, not a `uses:` step, so it is version-pinned rather than SHA-pinned. Reviewed OWASP LLM Top 10 and NIST AI RMF GenAI Profile for gate/rule updates — no new rule additions identified as obviously needed at this time. |
| 2026-07-18 | Name workflow jobs, add concurrency groups, and comment scoped permissions | Leave as-is (default zizmor persona already reported zero findings) | `zizmor --persona=auditor` surfaces low/info-level style findings beyond the default persona; addressed them opportunistically since the fixes were low-risk and keep the workflows auditor-clean too. |
