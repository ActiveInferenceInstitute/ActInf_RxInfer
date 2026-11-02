# Repository guidance

This repository is a small public Julia project environment for Active Inference and RxInfer.jl.

## Facts to preserve

- The project is defined by [`Project.toml`](Project.toml).
- The generative model is declared in [`specs/coin_flip.gnn.md`](specs/coin_flip.gnn.md) (Generalized Notation Notation) and is the single source of truth for the prior, observation count, and seed.
- The package is `src/ActInf_RxInfer.jl`; `src/spec_reader.jl` contains the dependency-free document reader and must not gain `using` statements.
- The runnable example is `examples/coin_flip.jl`; the test suite is `test/runtests.jl`; CI is `.github/workflows/ci.yml`.
- The upstream parser revision used by the validation gate is recorded in [`specs/gnn-pin.json`](specs/gnn-pin.json).
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
- Do not commit secrets, credentials, private paths, generated local manifests, or machine-specific artifacts. `Manifest.toml` and `docs/_build/` stay ignored.

## Verification

Run the documented gates and report them as they are, including "not run":

```sh
julia --project=. -e 'using Pkg; Pkg.test()'          # test suite, reads the committed GNN document
julia --project=. examples/coin_flip.jl               # example smoke check
python3 scripts/validate_gnn_spec.py --gnn-runtime <python> --julia julia --json
```

The GNN validation needs a runtime with the pinned GNN distribution (`--gnn-runtime` or `GNN_RUNTIME_PYTHON`, or a checkout via `--gnn-root`/`GNN_ROOT`). Without one it exits `2` and prints that the check was not run; that is not a pass. The recorded example output in the README and in `docs/getting_started.md` must stay consistent with an actual run on the resolved environment.
