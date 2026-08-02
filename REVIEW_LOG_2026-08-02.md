# REVIEW_LOG_2026-08-02

Docs-deep review and implementation pass for `ActInf_RxInfer`.

## Repository

- Repo: `ActiveInferenceInstitute/ActInf_RxInfer` (public)
- Default branch: `main` (origin/main)
- HEAD at start: `b880804` — "add .aii sidecar (100% complete) + CC-BY-4.0 LICENSE (InstituteOS metadata)"

## Phase 0 — Preflight

- `git fetch origin`; on `main`, up to date with `origin/main`; working tree clean.
- Inventory (tracked files, exactly 5):
  - `README.md` — 2-line stub ("# ActInf_RxInfer" + "Active Inference and RxInfer.jl")
  - `Project.toml` — `[deps]` only; no `name`, `uuid`, `version`, `[compat]`
  - `LICENSE` — MIT, Copyright (c) 2024 Active Inference Institute
  - `.gitignore` — standard Julia ignores (Manifest.toml, docs/build, coverage files)
  - `.aii/config.yaml` — InstituteOS sidecar (parses as valid YAML)
- Absent: `docs/`, `src/`, `test/`, `examples/`, `AGENTS.md`/`CLAUDE.md`, CI/`.github/`, `CITATION.cff`, `CONTRIBUTING.md`, `SECURITY.md`, any TODO/ROADMAP file.
- Local tooling: Julia 1.12.6 available. Registry resolution of the declared deps succeeded (see Phase 1).

## Phase 1 — Mega-deep docs review

Findings by severity (full scoped list in `TO-DO.md`):

- Minor (3):
  1. README is a bare stub: no badges, no structure, no external links, no license/citation info.
  2. Dead doc domains: `rxinfer.ml` and `docs.rxinfer.ml` return 404; RxInfer docs now live at `https://docs.rxinfer.com` (verified), examples at `https://examples.rxinfer.com` (verified).
  3. `https://github.com/ActiveInferenceInstitute/InstituteOS` returns 404 publicly (private or moved) — must not be linked as a public URL; federation can be described textually.
- Medium (5):
  1. `Project.toml` is not a valid package skeleton (no name/uuid/version) and has no `[compat]` bounds, so the environment is not reproducible across Julia versions.
  2. No `CITATION.cff`, despite citation metadata already present in `.aii/config.yaml`.
  3. No `CONTRIBUTING.md`.
  4. No `SECURITY.md`.
  5. No `AGENTS.md` for agent/tooling contributors.
- Major (1):
  1. No documentation tree at all (`docs/`), and no cross-linking between README, docs, license, and TODO.

External link verification (HTTP status, `curl -sL`, 2026-08-02):

| URL | Status |
| --- | --- |
| https://github.com/ActiveInferenceInstitute/ActInf_RxInfer | 200 |
| https://github.com/ActiveInferenceInstitute/Active_Inference_Ontology | 200 |
| https://github.com/ActiveInferenceInstitute | 200 |
| https://github.com/ReactiveBayes/RxInfer.jl | 200 |
| https://github.com/ReactiveBayes/ReactiveMP.jl | 200 |
| https://docs.rxinfer.com | 200 |
| https://docs.rxinfer.com/stable/ | 200 |
| https://examples.rxinfer.com | 200 |
| https://doi.org/10.21105/joss.05161 | 200 |
| https://www.activeinference.org | 200 |
| https://julialang.org | 200 |
| https://docs.julialang.org | 200 |
| https://en.wikipedia.org/wiki/Factor_graph | 200 |
| https://github.com/ActiveInferenceInstitute/InstituteOS | 404 (not linked) |
| https://rxinfer.ml | 404 (dead; replaced) |
| https://docs.rxinfer.ml | 404 (dead; replaced) |

Dependency resolution probe (Julia 1.12.6, General registry): Distributions v0.25.130, FileIO v1.20.0, Plots v1.41.6, ReactiveMP v6.3.3, RxInfer v5.5.0, StatsBase v0.34.12, StatsFuns v1.5.2, TupleTools v1.6.0. These ground the `[compat]` bounds added in this pass.

## Phase 2 — Scoping

Created `TO-DO.md` with Minor / Medium / Major sections (definitions included). See that file for the itemized, tracked scope.

## Phase 3 — Implementation

Commits (chronological; see `git log` for full hashes):

| Commit | Contents |
| --- | --- |
| `828b3e4` | `docs: add review log and scoped TO-DO for docs-deep pass` |
| `dcb41ea` | `chore: add Julia package metadata and compatibility bounds` |
| `70dbd3a` | `docs: add repository guides and contribution metadata` |
| `cd6bbf4` | `docs: finalize review findings and verification record` |
| `80cfcc2` | `docs: mark phase-4 verification complete` |

Notes:
- Heavy Julia work (full `Pkg.instantiate()`, running RxInfer models, precompilation) was intentionally NOT run — per pass guidance for Julia repos. Compat bounds are grounded in a registry resolution probe only.
- No source code was touched; the only non-doc change is `Project.toml` metadata (name/uuid/version/compat), verified by re-resolution.

## Phase 4 — Verification & push

- [x] Final link/status sweep of changed files (relative links, YAML/CFF parsing, stale-domain scan, `git diff --check`, Julia resolution)
- [x] `git status` contains only intended changes (11 files: 4 new docs, docs/ tree, Project.toml, README.md)
- [x] Pushed to `origin/main`
- [x] `git status` shows up to date with `origin/main`
