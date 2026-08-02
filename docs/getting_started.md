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

The project declares RxInfer.jl, ReactiveMP.jl, and supporting packages. It does not currently provide a source module, scripts, examples, or tests, so there is no repository-specific model or command to run yet.

For upstream usage documentation and runnable examples, see [RxInfer documentation](https://docs.rxinfer.com/) and [RxInfer examples](https://examples.rxinfer.com/).

## Reproducibility note

This repository intentionally does not commit `Manifest.toml` at present; it is ignored by [`.gitignore`](../.gitignore). The project-level version bounds in [`Project.toml`](../Project.toml) describe the supported dependency families. Once reproducible application or research runs are added, the repository should decide whether a committed manifest is appropriate for those workflows.
