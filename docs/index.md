# Documentation

This directory documents the Julia environment, the generative-model
specification, the verification gate, and the records the gate produces.

## Guides

- [Getting started](getting_started.md) — install Julia, activate the project, instantiate dependencies, run the example and tests, and inspect the environment.
- [Gate](gate.md) — the `./run.sh` arms (`lint`, `fast`, `full`, `docs`, `gnn`, `measure`), their environments, and the CI mapping.
- [Generalized Notation Notation](gnn.md) — the `specs/coin_flip.gnn.md` model declaration, the pinned parser record, and the validation commands.
- [Resources](resources.md) — links to the upstream RxInfer ecosystem and Active Inference references used by this repository.

## Generated records

- [Gate measurements](_generated/gate.md) — wall time and result per arm, rendered from [`_generated/gate-receipt.json`](_generated/gate-receipt.json) by `./run.sh measure`. Never edit it by hand; the `docs` arm checks it.

## Repository references

- [Documentation index](documentation-index.md) — flat list of the long-lived pages.
- [Folder entry point](README.md) — the shortest path into this directory.
- [Repository overview](../README.md)
- [Contribution guide](../CONTRIBUTING.md)
- [Security policy](../SECURITY.md)
- [Citation metadata](../CITATION.cff)
- [Open and completed review items](../TO-DO.md)
- [Documentation-deep review log](../REVIEW_LOG_2026-08-02.md)

## Current scope

The repository provides a Julia `Project.toml` with the dependencies used for Active Inference and RxInfer work, a package entry point (`src/ActInf_RxInfer.jl`) with the Beta-Bernoulli model, a dependency-free GNN reader (`src/spec_reader.jl`), a runnable example (`examples/coin_flip.jl`), a test suite (`test/runtests.jl`), one GitHub Actions workflow (`.github/workflows/ci.yml`), the pinned GNN conformance check (`scripts/validate_gnn_spec.py`), and one gate entry point (`run.sh`). Documentation describes these artifacts rather than behavior that does not yet exist.
