# Contributing

Thank you for contributing to ActInf_RxInfer.

## Before changing the repository

1. Read the [README](README.md) and [documentation index](docs/index.md).
2. Check [`TO-DO.md`](TO-DO.md) for documented follow-up work.
3. Confirm that the proposed change is grounded in the current repository and upstream package behavior.

## Development environment

The project uses Julia and declares its dependencies in [`Project.toml`](Project.toml). From the repository root:

```sh
julia --project=. -e 'using Pkg; Pkg.instantiate(); Pkg.status()'
```

The package is `src/ActInf_RxInfer.jl`, the suite is `test/runtests.jl`, and the example is `examples/coin_flip.jl`. When adding code, add corresponding tests and update the documentation in the same change.

## Before opening a pull request

Run the gate from the repository root and report the arms as they are:

```sh
./run.sh            # lint, then the fast arm (the default)
./run.sh all        # lint, full, docs, gnn
```

[`docs/gate.md`](docs/gate.md) lists every arm and what it proves. The `gnn` arm needs a pinned parser runtime or checkout, and exits `2` when it has neither; that is "not run", never a pass. `examples/coin_flip.jl` is exercised by the `full` arm.

## Documentation changes

- Keep commands consistent with the files and dependencies that actually exist.
- Prefer relative links for files in this repository.
- Verify external links before submitting.
- Do not add private paths, credentials, or claims that cannot be checked from the repository or a cited public source.

## Pull requests

Keep changes focused, describe what was verified, and include documentation for new public behavior. Review the repository's [security policy](SECURITY.md) rather than filing sensitive reports in a public pull request.

## License

By contributing, you agree that your contributions may be distributed under the repository's [MIT License](LICENSE).
