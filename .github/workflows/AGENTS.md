# AGENTS.md — `.github/workflows/`

- Keep `src/spec_reader.jl` dependency free; the conformance job runs it with a
  bare `julia` binary.
- The GNN job must install from `specs/gnn-pin.json` and verify the parser file
  digests. Do not replace it with a skip.
- `Pkg.test()` resolves from `Project.toml` because `Manifest.toml` is not
  committed; do not pin a version to hide a matrix failure.
- Actions stay pinned to full commit SHAs.
- Parent rules: [../../AGENTS.md](../../AGENTS.md).
