# TO-DO — ActInf_RxInfer

Scoped improvements from the docs-deep review pass.

- **Last reviewed:** 2026-08-02 (see `REVIEW_LOG_2026-08-02.md` for the full review and commit table)
- **Review scope:** documentation and docs-adjacent metadata. The repository now ships Julia source (`src/ActInf_RxInfer.jl`, `src/spec_reader.jl`), a runnable example, a test suite, and the pinned GNN validation gate, so later passes also cover the docs that describe them.

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
- [x] ✓ E7 — Add a verified runnable RxInfer example and the minimal package entry point: `examples/coin_flip.jl` (Beta-Bernoulli, RxInfer 5 `infer` API) and `src/ActInf_RxInfer.jl` (required so the named package precompiles). Verified on Julia 1.12.6 / RxInfer 5.5.0; measured output recorded in the docs and review log. — completed in `a4e0e39`.

## Major

- [x] ✓ L1 — Establish the `docs/` tree: index, getting-started guide (grounded in the verified environment), and curated resources page; wire cross-links README ↔ docs ↔ TO-DO ↔ CITATION. (`docs/index.md`, `docs/getting_started.md`, `docs/resources.md`) — completed in `70dbd3a`.

## Open / deferred

- [x] ✓ L2 — Adopt Generalized Notation Notation: declare the coin-flip model in `specs/coin_flip.gnn.md`, read it from `src/spec_reader.jl`, validate it with the pinned parser (`scripts/validate_gnn_spec.py`, `specs/gnn-pin.json`), and record the contract in `docs/gnn.md`. — completed in the GNN adoption change.
- [x] ✓ L3 — Add a test suite (`test/runtests.jl`) and CI (`.github/workflows/ci.yml`) covering the declared model, the conjugate posterior, and the pinned GNN conformance job. — completed in the GNN adoption change.
- [x] ✓ L4 — Bring the dependency bounds to the current families (RxInfer 6, ReactiveMP 7, StatsFuns 2, julia 1.10 long-term support floor) and re-verify the recorded example output. — completed in the GNN adoption change.
- **Next:** if a rendered target is wanted later, the discrete-POMDP family that GNN's RxInfer.jl renderer targets would need its own model in this repository; the conjugate model declared today is validated but not rendered.
- **Next:** the `inferants` branch holds a 2024 ants simulation (`ants.jl`) that was never merged and is preserved as is; adopting it would be a separate change.
