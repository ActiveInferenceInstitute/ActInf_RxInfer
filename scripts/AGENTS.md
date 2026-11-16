# AGENTS.md — `scripts/`

- Never import target GNN into the host validator. The reviewed bootstrap is
  stdlib-only and executes under a non-GNN identity; actual GNN imports and
  verdicts run in fresh selected-runtime children inside `qualified_source`
  through exit revalidation.
- Keep one producer-owned pin normalizer/checker and both independent frozen
  resource hashes; never infer expected identity from the target.
- Installed mode requires genuine distribution/PEP 610/full-content admission.
  Explicit source mode requires its selected package and runtime; no fallback.
- Keep exit codes `0` pass, `1` conformance failure, `2` not run. Do not return
  executable GNN objects for use outside their qualified lifetime.
- A model change updates the specification first, then this validator's
  expectations, in the same change.
- Parent rules: [../AGENTS.md](../AGENTS.md).
