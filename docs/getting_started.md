# Getting started

## Prerequisites

- [Julia 1.10 or later](https://julialang.org/downloads/)
- Git

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

The project declares RxInfer.jl, ReactiveMP.jl, and supporting packages, and provides:

- `src/ActInf_RxInfer.jl` — a minimal package entry point (loadable with `using ActInf_RxInfer`; it has no exported API yet).
- `examples/coin_flip.jl` — a verified Beta-Bernoulli "coin flip" example.

Run the example:

```sh
julia --project=. examples/coin_flip.jl
```

Verified output (Julia 1.12.6, RxInfer 5.5.0, fixed random seed):

```text
True bias:        0.75
Inferred mean:    0.7400793650793651
Inferred std:     0.01951703487781785
95% CI:           [0.7009483694712986, 0.7774057699488053]
```

There is no test suite yet; run repository tests once a suite exists.

For upstream usage documentation and runnable examples, see [RxInfer documentation](https://docs.rxinfer.com/) and [RxInfer examples](https://examples.rxinfer.com/).

## Reproducibility note

This repository intentionally does not commit `Manifest.toml` at present; it is ignored by [`.gitignore`](../.gitignore). The project-level version bounds in [`Project.toml`](../Project.toml) describe the supported dependency families. Once reproducible application or research runs are added, the repository should decide whether a committed manifest is appropriate for those workflows.
