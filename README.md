# ActInf_RxInfer

Active Inference and [RxInfer.jl](https://github.com/ReactiveBayes/RxInfer.jl).

[![License: MIT](https://img.shields.io/badge/License-MIT-blue.svg)](LICENSE)
[![Julia: 1.10+](https://img.shields.io/badge/Julia-1.10%2B-purple.svg)](https://julialang.org/)

## Status

This repository currently contains the Julia project environment for work connecting Active Inference with RxInfer.jl. It does not yet contain a `src/` directory, executable examples, or tests. The dependency environment is declared in [`Project.toml`](Project.toml) and is ready to be extended with source code and examples.

## Getting started

Install [Julia 1.10 or later](https://julialang.org/downloads/), clone the repository, and activate the project from its root:

```julia
using Pkg
Pkg.activate(".")
Pkg.instantiate()
Pkg.status()
```

The same commands can be run non-interactively:

```sh
julia --project=. -e 'using Pkg; Pkg.instantiate(); Pkg.status()'
```

See [`docs/getting_started.md`](docs/getting_started.md) for the environment workflow and [`docs/index.md`](docs/index.md) for the documentation map.

## Dependencies

The project declares [RxInfer.jl](https://github.com/ReactiveBayes/RxInfer.jl), [ReactiveMP.jl](https://github.com/ReactiveBayes/ReactiveMP.jl), and supporting Julia packages for probability distributions, statistics, plotting, file I/O, and linear algebra. Version bounds are recorded in `Project.toml`; the repository does not currently pin a committed `Manifest.toml`.

## Resources

- [RxInfer documentation](https://docs.rxinfer.com/)
- [RxInfer examples](https://examples.rxinfer.com/)
- [RxInfer.jl repository](https://github.com/ReactiveBayes/RxInfer.jl)
- [Active Inference Institute](https://www.activeinference.org/)
- [Documentation and resources in this repository](docs/index.md)

## Contributing

Read [`CONTRIBUTING.md`](CONTRIBUTING.md) before opening a change. Security reports are described in [`SECURITY.md`](SECURITY.md). Citation metadata is available in [`CITATION.cff`](CITATION.cff).

## License

This project is released under the [MIT License](LICENSE). Copyright © 2024 Active Inference Institute.
