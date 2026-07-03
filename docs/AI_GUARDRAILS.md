# AI Guardrails

Applies if this project builds prompts, calls LLMs, or processes untrusted content with AI.

## Instruction separation
System, developer, and user content are kept in separate message roles. Untrusted content (files, web, repo text, tool output) is never placed in the system prompt.

## Prompt injection
- Untrusted content is labeled as data, not instructions.
- Tool permissions are least-privilege; destructive actions require human approval.
- Outputs that trigger actions are validated before execution.

## Refusal / allow / deny rules
Document what the system must refuse, what requires approval, and what is auto-allowed.

## Evals
See docs/EVALS.md. Regression cases include known injection strings and jailbreak patterns relevant to this system.
