# Getting started

## Prerequisites

- [Julia 1.10 or later](https://julialang.org/downloads/) (1.10 is the current long-term support release)
- Git
- Python 3.10 or later, only for the pinned GNN validation script

The Julia version requirement is declared in [`Project.toml`](../Project.toml).

## Activate and instantiate

From the repository root, run:

```julia
using Pkg
Pkg.activate(".")
Pkg.instantiate()
Pkg.status()
```

Or use a one-shot shell command:

```sh
julia --project=. -e 'using Pkg; Pkg.instantiate(); Pkg.status()'
```

`Pkg.instantiate()` resolves and installs the dependencies declared by the project. `Pkg.status()` prints the resulting environment so that the installation can be checked.

## What is available now

- [`specs/coin_flip.gnn.md`](../specs/coin_flip.gnn.md) — the generative model declared in Generalized Notation Notation (GNN).
- `src/ActInf_RxInfer.jl` — the package: `spec_*` readers, `coin_model`, `coin_data`, `coin_posterior`, and `analytic_posterior`.
- `src/spec_reader.jl` — the dependency-free document reader.
- `examples/coin_flip.jl` — the runnable example.
- `test/runtests.jl` — the test suite.
- `scripts/validate_gnn_spec.py` — the pinned-parser conformance check.
- `run.sh` — the gate entry point; see [`gate.md`](gate.md).

Run the example:

```sh
julia --project=. examples/coin_flip.jl
```

Verified output (Julia 1.13.3, RxInfer 6.1.1, ReactiveMP 7.0.1, fixed random seed; the first line prints the absolute path of the document):

```text
Specification:    <repository>/specs/coin_flip.gnn.md
True bias:        0.75
Observations:     500 (371 successes)
Inferred mean:    0.7400793650793651
Inferred std:     0.01951703487781785
95% CI:           [0.7009483694712986, 0.7774057699488053]
Conjugate mean:   0.7400793650793651
Conjugate std:    0.01951703487781785
```

The inferred posterior equals the closed-form conjugate posterior `Beta(a + k, b + n - k)` for these observations; the test suite asserts that equality.

Run the tests:

```sh
./run.sh fast        # suite without the message-passing testsets
./run.sh full        # every testset, through Pkg.test()
```

`./run.sh` is the gate entry point; it runs the commands CI runs, and
[`gate.md`](gate.md) lists every arm. `./run.sh` with no argument runs `lint`
and then `fast`.

Validate the committed document with the pinned upstream parser:

```sh
./run.sh gnn
```

That arm needs a pinned parser runtime or checkout; without one it exits `2` and
reports the check as not run. `GNN_ROOT` and `GNN_PYTHON` select a checkout, and
`GNN_RUNTIME_PYTHON` an installed runtime; otherwise the arm provisions
`specs/gnn-pin.json` with `uv`. The local reader requires the pin's
`gnn-importer-pin/v1` schema. See [`gnn.md`](gnn.md) for the pin, the validated
modes, and the exit codes.

For upstream usage documentation and runnable examples, see [RxInfer documentation](https://docs.rxinfer.com/) and [RxInfer examples](https://examples.rxinfer.com/).

## Reproducibility note

This repository intentionally does not commit `Manifest.toml`; it is ignored by [`.gitignore`](../.gitignore). The project-level version bounds in [`Project.toml`](../Project.toml) describe the supported dependency families, and the recorded example output names the versions it was produced with. Once reproducible application or research runs are added, the repository should decide whether a committed manifest is appropriate for those workflows.
