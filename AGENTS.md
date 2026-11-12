# Repository guidance

This repository is a small public Julia project environment for Active Inference and RxInfer.jl.

## Facts to preserve

- The project is defined by [`Project.toml`](Project.toml).
- The generative model is declared in [`specs/coin_flip.gnn.md`](specs/coin_flip.gnn.md) (Generalized Notation Notation) and is the single source of truth for the prior, observation count, and seed.
- The package is `src/ActInf_RxInfer.jl`; `src/spec_reader.jl` contains the dependency-free document reader and must not gain `using` statements.
- The runnable example is `examples/coin_flip.jl`; the test suite is `test/runtests.jl`; the gate entry point is `run.sh`; CI is `.github/workflows/ci.yml` and runs `run.sh` arms.
- The upstream parser revision used by the validation gate is recorded in [`specs/gnn-pin.json`](specs/gnn-pin.json). The pin, the pointer and the document are validated by the shared `gnn.importers` reader from that pinned revision, run by `run.sh gnn`; this repository keeps no copy of it.
- The public license is [MIT](LICENSE).
- Documentation starts at [`docs/index.md`](docs/index.md).
- Review scope and deferred work are tracked in [`TO-DO.md`](TO-DO.md).

## Change conventions

- Inspect the current files before editing; do not invent APIs, examples, results, or paths.
- Keep public documentation grounded in repository contents or linked public upstream sources.
- Use relative links for repository files and verify external links when changing them.
- Keep dependency changes in `Project.toml` and document their purpose.
- Change the model in `specs/coin_flip.gnn.md` first, then the reader expectations in `scripts/validate_gnn_spec.py`, the recorded example output, and the docs in the same change. Never leave the document describing a model the code does not implement.
- When source code or tests change, update the getting-started guide and this file.
- Add gate behavior to `run.sh` and document it in `docs/gate.md`; never put a second copy of an arm's command in the workflow or the docs.
- Do not hand-write measured numbers. `./run.sh measure` writes `docs/_generated/gate.md`, and the `docs` arm fails when the table disagrees with its receipt.
- Do not commit secrets, credentials, private paths, generated local manifests, or machine-specific artifacts. `Manifest.toml` and `docs/_build/` stay ignored.

## Verification

`./run.sh` is the only gate entry point; every arm runs one command and CI runs
the same script (`docs/gate.md` documents each arm, CI job, and environment).

```sh
./run.sh lint                                        # syntax checks, no package loading
./run.sh fast                                        # suite without message passing
./run.sh full                                        # full suite through Pkg.test()
./run.sh docs                                        # links, docs hub, generated numbers
./run.sh gnn                                         # pinned GNN conformance
./run.sh measure                                     # refresh docs/_generated/gate.md
```

Report each arm as it is, including "not run". The `gnn` arm needs a runtime:
`GNN_RUNTIME_PYTHON` for an installed one, or `uv` to provision the pin (from
`GNN_ROOT` when that names a checkout). Without one it exits `2` and prints that
the check was not run; that is not a pass. The example is exercised by the `full`
arm, which includes [`examples/coin_flip.jl`](examples/coin_flip.jl) in its last
testset. Wall times are measured, not estimated: run `./run.sh measure` and read
[`docs/_generated/gate.md`](docs/_generated/gate.md) instead of writing a number
into prose.
