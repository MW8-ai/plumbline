# Adapter roadmap

## v0 (this) — annotate
Transform script only. Failing systems appear via a GOV scope ring using
Anatomy's existing catalog-driven scopes (meta.scopes) — zero renderer changes.
Per-node detail rides in node.gov and shows wherever the catalog cross-section
displays node fields.

## v0.1 — render (small Anatomy patch, Claude Code task)
Governance overlay toggle in Anatomy: stain nodes by gov.status
(pass/warn/fail/unknown), tooltip lists failing gates, meta.governance.asOf
in the title block. Vanilla JS, no build step, same constraints as always.

## v0.2 — automate
CI step in each governed repo publishes report.json as an artifact; a nightly
job in the Anatomy repo pulls artifacts, runs the adapter, commits the
annotated catalog. The wall diagram now updates itself.

## v1 — living network
Second ingest adapter: Azure Resource Graph query -> catalog nodes/edges.
Same catalog contract, real estate instead of hand-authored test catalogs.
This is the answer to "plug into a living network": Anatomy doesn't need to
BE live, its catalog needs live writers. ARG for Azure first (interview-
relevant), CloudQuery or provider APIs for the agnostic story later.

## Explicitly not building
A web platform around this. The catalog JSON is the platform.
