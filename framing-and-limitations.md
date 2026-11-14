# Framing and limitations

This note keeps the preserved Gemini proposal in perspective. It exists so the proposal is not mistaken for more than it is.

## What this is not

- **Not validated.** The proposal is an AI-generated response. None of its claims have been tested, benchmarked, or reviewed against published evidence.
- **No novelty claim.** This document establishes nothing about whether any part of the proposal is new. Requirements traceability is an established topic in software engineering; determining what is already known would require a literature and tooling review that has not been done here.
- **Not a commitment.** No implementation, study, user research, or recruitment is planned or implied by keeping this record.

## Claims to treat carefully

- **Semantic similarity is not proof of coverage.** Embedding-based links between requirements and code are heuristic matches. A strong semantic link does not prove a requirement is implemented, and a weak one does not prove it is missing. Any system built on these ideas would need to distinguish inferred links from verified evidence and to measure precision and recall against human-confirmed traces.
- **The two directions may not be symmetric.** Forward coverage (every requirement has implementing code) and backward justification (every piece of code maps to a requirement) have different failure modes and would each need their own verification approach.
- **Terminology ambiguity.** The proposal mentions "Concur docs" alongside Markdown and PDF as sources of requirements. The wording is reproduced verbatim; the intended referent is ambiguous and has not been verified.
- **Automated CI flagging is a risk to evaluate, not a given.** The proposal's "agentic maintenance" step depends on link quality good enough to act on in a pipeline. Whether that holds is an open question that would need evaluation on real projects before the step could be trusted.

## Suggested next checks before taking this further

1. Survey existing requirements-traceability research and tools to establish what is already known.
2. Decide whether the goal is a tool, a paper, or both - they have different evidence bars.
3. If a tool: prototype on one small real project and measure inferred-link accuracy against hand-traced ground truth before trusting CI automation.
