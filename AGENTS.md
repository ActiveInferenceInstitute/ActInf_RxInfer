# Repository guidance

This repository is a small public Julia project environment for Active Inference and RxInfer.jl.

## Facts to preserve

- The project is defined by [`Project.toml`](Project.toml).
- The generative model is declared in [`specs/coin_flip.gnn.md`](specs/coin_flip.gnn.md) (Generalized Notation Notation) and is the single source of truth for the prior, observation count, and seed.
- The package is `src/ActInf_RxInfer.jl`; `src/spec_reader.jl` contains the dependency-free document reader and must not gain `using` statements.
- The runnable example is `examples/coin_flip.jl`; the test suite is `test/runtests.jl`; the gate entry point is `run.sh`; CI is `.github/workflows/ci.yml` and runs `run.sh` arms.
- The unchanged upstream revision is recorded in [`specs/gnn-pin.json`](specs/gnn-pin.json). The independently checked standalone producer normalizes the pin and checks the pin/pointer/document. `scripts/gnn_source.py` freezes the bootstrap and complete matching-manifest digests; target imports and verdict calls require the producer's qualified lifetime. `run.sh` is the sole arm authority.
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
- `full` must explicitly select the full suite regardless of inherited `ACTINF_RXINFER_TEST_ARM`. Provisioning must invalidate stale success markers before mutation and publish a replacement only after every step succeeds; `test/test_run_gate.py` covers these transitions.
- Keep checked-bootstrap and complete-manifest admission across every direct and child entry. Execute the same checked bytes under a non-GNN identity and keep actual GNN calls inside qualification through exit revalidation. Installed-origin failure never authorizes source fallback. Explicit-source proof does not certify an installed runtime, hosted delivery or scientific execution.
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

Report every arm as it is, including "not run". The GNN arm requires independent
`GNN_BOOTSTRAP` and `GNN_SOURCE_MANIFEST` resources. Installed mode selects
`GNN_RUNTIME_PYTHON` or uses the existing `uv` provisioning path; genuine
distribution ownership, exact Git PEP 610 and complete content must pass.
Explicit `GNN_ORIGIN_MODE=source` requires a runtime and `GNN_PACKAGE_ROOT`
and reports narrower evidence. Missing resources or admission exit `2`, never pass.
The GNN arm checks the live tag by default. For an offline launch, prepare
the pinned tag in a Git store with the upstream origin and pass
`GNN_TAG_STORE` as described in [the gate guide](docs/gate.md).
The example is exercised by the `full` arm, which includes [`examples/coin_flip.jl`](examples/coin_flip.jl) in its last
testset. Wall times are measured, not estimated: run `./run.sh measure` and read
[`docs/_generated/gate.md`](docs/_generated/gate.md) instead of writing a number
into prose.
