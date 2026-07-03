# Decision Log

| Date | Decision | Alternatives considered | Why |
|------|----------|------------------------|-----|
| 2026-07-03 | SHA-pin all GitHub Actions in workflows | Leave tag refs | Tags are mutable; SHA pins prevent supply-chain attacks. zizmor flags unpinned refs. |
| 2026-07-03 | Add `iac_scan` gate (checkov-based) | semgrep, tfsec | checkov covers Terraform, Bicep, and CloudFormation; skips politely when absent. |
| 2026-07-03 | Add `foundry_iac` profile | Extend `default` | Keeps profiles composable; foundry repos opt in without affecting other profiles. |
| 2026-07-03 | Add `.github/copilot-instructions.md` | CLAUDE.md / AGENTS.md | Copilot's equivalent governance file; same rules as sibling repos. |
| 2026-07-03 | Bump version to 0.2.0 | Stay at 0.1.x | SHA-pinning + new gate is a backwards-compatible feature addition warranting a minor bump. |
