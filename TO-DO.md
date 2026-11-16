# TO-DO — ActInf_RxInfer

Scoped improvements from the docs-deep review pass.

- **Last reviewed:** 2026-11-12 (see `REVIEW_LOG_2026-08-02.md` for the original review and commit table; the later passes are recorded in the commit log, most recently `2d69bf6`)
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
- [x] ✓ E2 — Harden `Project.toml`: add `name`, `uuid`, `version`, and `[compat]` bounds grounded in the registry resolution probe (RxInfer 5, ReactiveMP 6, Distributions 0.25, Plots 1, StatsBase 0.34, StatsFuns 1, TupleTools 1, FileIO 1, julia 1.10). (`Project.toml`) — completed in `dcb41ea`; those bounds were superseded by L4, and `Plots` and `FileIO` have since left `Project.toml` entirely.
- [x] ✓ E3 — Add `CITATION.cff` with institute-level authorship (grounded in `LICENSE` and `.aii/config.yaml`). (`CITATION.cff`) — completed in `70dbd3a`.
- [x] ✓ E4 — Add `CONTRIBUTING.md` (fork/PR flow, development environment, documentation conventions). (`CONTRIBUTING.md`) — completed in `70dbd3a`.
- [x] ✓ E5 — Add `SECURITY.md` (private vulnerability reporting via GitHub advisory URL for this repo). (`SECURITY.md`) — completed in `70dbd3a`.
- [x] ✓ E6 — Add `AGENTS.md` with repository facts and conventions for AI agent and tooling contributors. (`AGENTS.md`) — completed in `70dbd3a`.
- [x] ✓ E7 — Add a verified runnable RxInfer example and the minimal package entry point: `examples/coin_flip.jl` (Beta-Bernoulli, RxInfer 5 `infer` API) and `src/ActInf_RxInfer.jl` (required so the named package precompiles). Verified then on Julia 1.12.6 / RxInfer 5.5.0 and re-verified under the current bounds (Julia 1.13.3 / RxInfer 6.1.1 / ReactiveMP 7.0.1, output recorded in `README.md`); the model is now declared in `specs/coin_flip.gnn.md` rather than in the script. — completed in `a4e0e39`, re-verified in `dbfd747`.

## Major

- [x] ✓ L1 — Establish the `docs/` tree: index, getting-started guide (grounded in the verified environment), and curated resources page; wire cross-links README ↔ docs ↔ TO-DO ↔ CITATION. (`docs/index.md`, `docs/getting_started.md`, `docs/resources.md`) — completed in `70dbd3a`.
- [x] ✓ L5 — One gate entry point (`run.sh`) with separately runnable `lint`, `fast`, `full`, `docs`, `gnn`, and `measure` arms; CI runs the same arms instead of its own copies of the commands, the GNN runtime is provisioned from `specs/gnn-pin.json` by the `gnn` arm, and measured wall times live in the generated [`docs/_generated/gate.md`](docs/_generated/gate.md). — completed in `f760189` (#12); the per-arm failure propagation followed in `5fef340` (#13). `./run.sh docs` passes on 2026-11-12 (`docs: checked 37 markdown files` · `docs: clean` · `gate: docs/_generated/gate.md matches its receipt`).

## Open / deferred

- [x] ✓ L2 — Adopt Generalized Notation Notation: declare the coin-flip model in `specs/coin_flip.gnn.md`, read it from `src/spec_reader.jl`, validate it with the pinned parser (`scripts/validate_gnn_spec.py`, `specs/gnn-pin.json`), and record the contract in `docs/gnn.md`. — completed in `dbfd747` (merged as #2, `7452645`); the pin then moved to the canonical `gnn-importer-pin/v1` schema in `e55a236` (#10) with the pointer documented in `6326ffe` (#11).
- [x] ✓ L3 — Add a test suite (`test/runtests.jl`) and CI (`.github/workflows/ci.yml`) covering the declared model, the conjugate posterior, and the pinned GNN conformance job. — completed in `dbfd747` (merged as #2, `7452645`); `test/test_gnn_pin.py` was removed with the cutover in `2d69bf6` (#14), so `test/runtests.jl` is the checked contract.
- [x] ✓ L4 — Bring the dependency bounds to the current families (RxInfer 6, ReactiveMP 7, StatsFuns 2, julia 1.10 long-term support floor) and re-verify the recorded example output. — completed in `dbfd747`; the current `Project.toml` carries `RxInfer = "6"`, `ReactiveMP = "7"`, `StatsFuns = "2"`, `julia = "1.10"`.
- [x] ✓ L6 — Complete the GNN–FEP cutover: advance `specs/gnn-pin.json` from `v5.0.3` (`8f293d9ba`) to `v5.1.0` (`75c834bd8`), delete the local pin reader and its pin-shape tests, and run the estate's shared `gnn.importers` reader from the pinned runtime before the model-conformance step. — completed in `2d69bf6` (#14). `specs/gnn-pin.json` records tag `v5.1.0` at `75c834bd8519dc7b5adc4d24f16bf393cfd1ecdf` with the `src/gnn/importers.py` digest, `test/test_gnn_pin.py` is gone, and `./run.sh gnn` runs both steps in that one pinned environment. The order this item originally described — the reader before `scripts/validate_gnn_spec.py` — was a defect: the reader imports the pinned parser and validates the document with it, so the digest verification has to run first, and both steps now run with `-P` so the package verified is the package parsed.
- [x] ✓ L7 — Verify the pinned parser digests *before* anything imports it, and verify the package that is actually parsed. The arm ran the shared reader first, which validates the document with `gnn.parsers.basic.validate_gnn_syntax`, and the digests were checked against the package `python -c` resolves (the working directory) rather than the one the probe imports (`scripts/`). Reproduced against a copy of `.gate/gnn-runtime` with one pinned file tampered; the repair runs the validator before the reader and runs every subprocess that imports the package with `-P`. — completed in #19, with the end-to-end regression test `test/test_gnn_verification_order.py` wired into the arm's existing `unittest discover`. Open residual: `read_pin` necessarily imports `gnn.importers` from the installed package to normalize the pin, so that one import precedes the digest check; closing it would mean reading `parser_files` out of the pin without the shared reader, which the L6 cutover deliberately removed.
- [x] O1 — Remove public links to the private InstituteOS repository. The handwritten README describes it textually, and the qualified canonical platform renderer now produces the same public-safe boundary in `.aii/README.md`. Its actual generated output passed completeness validation and is applied unchanged; ecosystem relations remain intact.
- [ ] O2 — Review retirement of `workflows/gnn-fep-migration` and `estate/audit-fixes` with a maintainer. Prior review recorded redundant or superseded changes, but deletion requires a fresh preservation check and explicit authorization. No remote branches were deleted.
- **Next:** if a rendered target is wanted later, the discrete-POMDP family that GNN's RxInfer.jl renderer targets would need its own model in this repository; the conjugate model declared today is validated but not rendered.
- **Next:** the `inferants` branch holds a 2024 ants simulation (`ants.jl`) that was never merged and is preserved as is; adopting it would be a separate change.

## Gate reliability review — 2026-11-13

- [x] R1 — Force the full Julia test arm despite an inherited `fast` setting. Verified with the actual Julia package suite and example, not only dispatcher fixtures.
- [x] R2 — Propagate provisioning failures, invalidate stale markers before mutation, reuse a matching cache and publish success atomically. Offline regression cases cover failure transitions and dispatch; they do not qualify a GNN installation.
- [ ] R3 — Pre-import caller cutover at the unchanged v5.1.0 pin is implemented and governed local real-source/process admission plus affected dispatch regressions pass. All callers use the independently checked producer and complete manifest through exit revalidation. Installed distribution/PEP 610, full tag/Julia GNN-arm acceptance and hosted resource delivery remain separate obligations; explicit-source evidence does not close them. Preserve historical L6/L7 receipts and see `docs/gnn.md`.
- [x] R4 — Replace deprecated array-quantile calls with upstream-recommended scalar mapping. The actual full Julia suite and example pass with an inherited `fast` setting; the scientific model, dependency bounds and historical recorded output remain unchanged.

## Canonical sidecar regeneration — 2026-11-16

- [x] Regenerated the five projections from current metadata with the canonical
  producer after its path-base and Markdown repairs. Completeness validation passed;
  applied documents preserve the generator's exact bytes. `docs[]` is explicitly
  sidecar-relative, unlike repository-relative artifact paths.
- [ ] Repository docs/GNN gates, R3 installed-runtime and hosted-resource prerequisites
  remain separate; generation is not a full-gate, scientific or publication verdict.
