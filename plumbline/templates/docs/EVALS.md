# Evals

## What is measured
Accuracy, refusal correctness, injection resistance, output format validity.

## Golden set
Location of test cases and expected outputs. Every bug that reaches production becomes a regression case here.

## Cadence
Run on every PR touching prompts or models; full sweep on release via Batch API (50% cost).
