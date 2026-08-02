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

There is currently no source package or test suite in this repository. When adding code, add corresponding tests and update the documentation in the same change.

## Documentation changes

- Keep commands consistent with the files and dependencies that actually exist.
- Prefer relative links for files in this repository.
- Verify external links before submitting.
- Do not add private paths, credentials, or claims that cannot be checked from the repository or a cited public source.

## Pull requests

Keep changes focused, describe what was verified, and include documentation for new public behavior. Review the repository's [security policy](SECURITY.md) rather than filing sensitive reports in a public pull request.

## License

By contributing, you agree that your contributions may be distributed under the repository's [MIT License](LICENSE).
