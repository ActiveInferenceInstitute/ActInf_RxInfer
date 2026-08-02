# TO-DO — ActInf_RxInfer

Scoped improvements from the docs-deep review pass.

- **Last reviewed:** 2026-08-02 (see `REVIEW_LOG_2026-08-02.md` for the full review and commit table)
- **Review scope:** documentation and docs-adjacent metadata only; no source code exists yet in this repository

Severity definitions:

- **Minor** — typo, broken link, formatting.
- **Medium** — stale section rewrite, doc restructure, added missing guide.
- **Major** — large doc system overhaul, new documentation site, cross-cutting refactors.

## Minor

- [x] ✓ M1 — README is a bare two-line stub; add structure, static badges (MIT license, Julia), and verified external links. (`README.md`) — completed in `70dbd3a`.
- [x] ✓ M2 — Dead doc domains `rxinfer.ml` / `docs.rxinfer.ml`; use verified `https://docs.rxinfer.com` and `https://examples.rxinfer.com` everywhere. (`docs/`, `README.md`) — completed in `70dbd3a`.
- [x] ✓ M3 — InstituteOS GitHub URL returns 404 publicly; do not link it, describe the federation textually only. (`docs/resources.md`, `README.md`) — completed in `70dbd3a`.

## Medium

- [x] ✓ E1 — Rewrite README.md as a complete repository overview: purpose, honest status (environment skeleton, no `src/`), prerequisites, install, usage pointers, resources, license, citation, related repositories. (`README.md`) — completed in `70dbd3a`.
- [x] ✓ E2 — Harden `Project.toml`: add `name`, `uuid`, `version`, and `[compat]` bounds grounded in the registry resolution probe (RxInfer 5, ReactiveMP 6, Distributions 0.25, Plots 1, StatsBase 0.34, StatsFuns 1, TupleTools 1, FileIO 1, julia 1.10). (`Project.toml`) — completed in `dcb41ea`.
- [x] ✓ E3 — Add `CITATION.cff` with institute-level authorship (grounded in `LICENSE` and `.aii/config.yaml`). (`CITATION.cff`) — completed in `70dbd3a`.
- [x] ✓ E4 — Add `CONTRIBUTING.md` (fork/PR flow, development environment, documentation conventions). (`CONTRIBUTING.md`) — completed in `70dbd3a`.
- [x] ✓ E5 — Add `SECURITY.md` (private vulnerability reporting via GitHub advisory URL for this repo). (`SECURITY.md`) — completed in `70dbd3a`.
- [x] ✓ E6 — Add `AGENTS.md` with repository facts and conventions for AI agent and tooling contributors. (`AGENTS.md`) — completed in `70dbd3a`.

## Major

- [x] ✓ L1 — Establish the `docs/` tree: index, getting-started guide (grounded in the verified environment), and curated resources page; wire cross-links README ↔ docs ↔ TO-DO ↔ CITATION. (`docs/index.md`, `docs/getting_started.md`, `docs/resources.md`) — completed in `70dbd3a`.

## Open / deferred

- Heavy Julia work (full `Pkg.instantiate()`, running RxInfer models, precompilation, test suites) is deferred — no `src/`/`test/` exists, and per pass guidance Julia-heavy runs are skipped. Compat bounds were verified via registry resolution only (see `REVIEW_LOG_2026-08-02.md`).
- No other open items.
