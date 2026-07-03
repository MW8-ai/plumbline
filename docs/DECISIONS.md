# Decision Log

| Date | Decision | Alternatives considered | Why |
|------|----------|------------------------|-----|
| 2026-07-03 | SHA-pin all GitHub Actions | Keep floating version tags | Floating tags are mutable; pinning to a commit SHA prevents supply-chain attacks where a tag is silently moved to malicious code. Version kept as trailing comment for readability. |
| 2026-07-03 | Add `iac_scan` gate (checkov-based) | Integrate Terraform linting via tflint | checkov covers multiple IaC formats (Terraform, Bicep) and maps findings to severity levels we already use. Skips politely when checkov is not installed. |
| 2026-07-03 | Add `foundry_iac` profile | Extend `default` profile | IaC repos have distinct concerns; a dedicated profile avoids bloating the default and makes the intent explicit. |
