# Repository guidance

This repository is a small public Julia project environment for Active Inference and RxInfer.jl.

## Facts to preserve

- The project is defined by [`Project.toml`](Project.toml).
- The repository provides a minimal `src/ActInf_RxInfer.jl` entry point and a verified example (`examples/coin_flip.jl`); there is no `test/` tree yet.
- The public license is [MIT](LICENSE).
- Documentation starts at [`docs/index.md`](docs/index.md).
- Review scope and deferred work are tracked in [`TO-DO.md`](TO-DO.md).

## Change conventions

- Inspect the current files before editing; do not invent APIs, examples, results, or paths.
- Keep public documentation grounded in repository contents or linked public upstream sources.
- Use relative links for repository files and verify external links when changing them.
- Keep dependency changes in `Project.toml` and document their purpose.
- When source code or tests are added, update the relevant getting-started and contributor documentation.
- Do not commit secrets, credentials, private paths, generated local manifests, or machine-specific artifacts.

## Verification

For documentation-only changes, check links and inspect the rendered Markdown structure. For Julia project changes, run a lightweight project resolution or status check when practical; the example in `examples/coin_flip.jl` serves as a smoke check (`julia --project=. examples/coin_flip.jl`). Run any repository tests once a test suite exists; do not claim tests passed when no tests exist.
