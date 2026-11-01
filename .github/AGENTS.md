# CI guidance

The workflow runs the Julia test suite on the long-term support release (1.10)
and on stable, and a separate `gnn conformance` job validates
`specs/coin_flip.gnn.md`.

- `src/spec_reader.jl` must stay dependency free: the conformance job runs it
  with a bare `julia` binary and compares what it reads with the pinned GNN
  parser and the expectations in `scripts/validate_gnn_spec.py`.
- The `gnn conformance` job provisions the GNN revision pinned in
  `specs/gnn-pin.json` (currently v5.0.3, commit `8f293d9ba`) into its own
  Python runtime and digest-verifies the installed parser files before parsing.
  It is a required check and must not be converted into a skip when the runtime
  cannot be provisioned.
- The test matrix runs `Pkg.test()`, which resolves dependencies from
  `Project.toml` because `Manifest.toml` is intentionally not committed. A
  failure on either matrix entry is a real failure; do not pin a version to
  hide it.
