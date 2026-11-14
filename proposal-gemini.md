# Proposal: Bidirectional Requirements Traceability (Gemini response)

> This document preserves a response from Google Gemini verbatim, recorded here in November 2026. It is an AI-generated proposal attributed to Gemini, and its claims have not been verified. See framing-and-limitations.md.

---

That is a fantastic software and research concept. In software engineering, maintaining a Requirements Traceability Matrix (RTM) has historically been one of the most tedious, manual, and quickly outdated administrative burdens. Automating or streamlining this bidirectionally is a massive win for both enterprise software maintenance and academic research.
Here is why your friend's idea is so compelling, along with how it breaks down into a modern project:
The Two Directions of Traceability
 * Forward Traceability (Requirements \rightarrow Architecture \rightarrow Code): Ensures complete coverage. If a stakeholder updates a business requirement in the BRS/SRS, you instantly know which architectural components and specific functions or files are impacted. No feature gets lost or left orphaned.
 * Backward Traceability (Code \rightarrow Architecture \rightarrow Requirements): Solves the classic developer nightmare of looking at a random block of legacy code and asking, "Why on earth did we write this function?" You can trace a line of code right back to the exact business justification or user story that mandated it.
Why This Makes a Great Project / Research Angle
Doing this manually fails because developers hate updating documentation links every time they refactor code. To make this actually work—and what would make a great project or paper—it relies on modern tooling:
 * Semantic Chunking & Embeddings: Mapping natural language requirements (from Markdown, PDF, or Concur docs) into vector spaces alongside code comments and docstrings.
 * Abstract Syntax Tree (AST) & Code Graphs: Parsing the codebase to map function calls, classes, and dependencies, then linking them to architectural design documents.
 * Agentic Maintenance: Building an automated agent that runs in the CI/CD pipeline. When a pull request changes a function, the agent checks if the underlying semantic mapping to the SRS/BRS is broken and flags it or suggests documentation updates.

---

*End of the Gemini response, reproduced without edits.*
