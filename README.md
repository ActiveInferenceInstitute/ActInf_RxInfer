# ActInf_RxInfer

Active Inference and [RxInfer.jl](https://github.com/ReactiveBayes/RxInfer.jl).

[![CI](https://github.com/ActiveInferenceInstitute/ActInf_RxInfer/actions/workflows/ci.yml/badge.svg)](https://github.com/ActiveInferenceInstitute/ActInf_RxInfer/actions/workflows/ci.yml)
[![License: MIT](https://img.shields.io/badge/License-MIT-blue.svg)](LICENSE)
[![Julia: 1.10+](https://img.shields.io/badge/Julia-1.10%2B-purple.svg)](https://julialang.org/)

## Contents

- [Status](#status)
- [Generative-model specification](#generative-model-specification)
- [Getting started](#getting-started)
- [Example](#example)
- [Tests](#tests)
- [Dependencies](#dependencies)
- [Resources](#resources)
- [Contributing](#contributing)
- [License](#license)
- [InstituteOS sidecar](#instituteos-sidecar)

## Status

This repository provides a Julia project environment for work connecting Active Inference with RxInfer.jl, the Beta-Bernoulli coin-flip model as a [Generalized Notation Notation](https://github.com/ActiveInferenceInstitute/Generalized_Notation_Notation) (GNN) document, a package entry point that reads that document, a runnable example, and a test suite. The dependency environment is declared in [`Project.toml`](Project.toml). [`run.sh`](run.sh) is the gate entry point, and CI runs its arms: `./run.sh full` on the long-term support release and on stable, `./run.sh lint` and `./run.sh docs` in one static job, and `./run.sh gnn` as a required conformance job.

## Generative-model specification

The model is declared in [`specs/coin_flip.gnn.md`](specs/coin_flip.gnn.md): latent bias `theta ~ Beta(a, b)`, observations `y_i ~ Bernoulli(theta)`, the sufficient statistic `k = sum(y)`, and the closed-form conjugate posterior `theta | y ~ Beta(a + k, b + n - k)`. The Julia code reads the declared prior, observation count, and seed instead of repeating them: `spec_parameters(SPEC_PATH)` loads them through the dependency-free reader [`src/spec_reader.jl`](src/spec_reader.jl).

[`scripts/validate_gnn_spec.py`](scripts/validate_gnn_spec.py) checks the document with the parser pinned in [`specs/gnn-pin.json`](specs/gnn-pin.json) (GNN v5.0.3, commit `8f293d9ba`) and with the Julia reader, so all three readers must agree. CI runs it as a required job. See [`docs/gnn.md`](docs/gnn.md).

GNN maintains a [downstream adoption
guide](https://github.com/ActiveInferenceInstitute/Generalized_Notation_Notation/blob/main/docs/gnn/integration/downstream_adoption.md)
for repositories that consume the notation.

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

## Example

A verified Beta-Bernoulli "coin flip" example ([`examples/coin_flip.jl`](examples/coin_flip.jl)) estimates the bias of a coin by message-passing inference and compares the result with the conjugate posterior:

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

## Tests

[`run.sh`](run.sh) is the single gate entry point; each arm runs one command and CI calls the same script. [`docs/gate.md`](docs/gate.md) describes every arm, and [`docs/_generated/gate.md`](docs/_generated/gate.md) records the measured wall time of each one.

```sh
./run.sh             # lint, then the fast arm
./run.sh full        # every testset, through Pkg.test()
./run.sh gnn         # the pinned GNN conformance check
```

The `fast` arm runs the suite without the two testsets that start RxInfer message passing. The `full` arm runs `julia --project=. -e 'using Pkg; Pkg.test()'`, and the suite reads the committed GNN document and checks the declared model, the reader's error paths, reproducible data generation, and that message passing reproduces the closed-form conjugate posterior. The `gnn` arm resolves the parser pinned in [`specs/gnn-pin.json`](specs/gnn-pin.json); it accepts `GNN_ROOT`/`GNN_PYTHON` for a checkout, `GNN_RUNTIME_PYTHON` for an installed runtime, and otherwise provisions the pin with `uv`. Without any of those it reports that the check was not run and exits `2`.

## Dependencies

The project declares [RxInfer.jl](https://github.com/ReactiveBayes/RxInfer.jl) 6, [ReactiveMP.jl](https://github.com/ReactiveBayes/ReactiveMP.jl) 7, and supporting Julia packages for probability distributions and statistics. Version bounds are recorded in `Project.toml`; the repository does not pin a committed `Manifest.toml`. `Plots` and `FileIO` are no longer declared: nothing in the package, examples, or tests used them, and their native dependencies (Qt, FFMPEG, GR) do not resolve on every host. Add them to your environment with `Pkg.add("Plots")` if you want them.

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

## InstituteOS sidecar

This repository carries a committed [`.aii/`](.aii/README.md) sidecar with curated
InstituteOS metadata (`aii-sidecar/v1`): category, maturity, ecosystem relations,
key artifacts, provenance, and portable tasks. It is read by
[InstituteOS](https://github.com/ActiveInferenceInstitute/InstituteOS) tooling and
does not affect the project's build or runtime.
