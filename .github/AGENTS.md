# CI guidance

The workflow runs three jobs, and each one runs an arm of `./run.sh` rather than
its own copy of a command:

- `test (julia <version>)` — `./run.sh full`, the `Pkg.test()` suite, on the
  long-term support release (1.10) and on stable.
- `static (lint, docs)` — `./run.sh lint`, then `./run.sh docs`. It uses the
  runner's `python3` and installs nothing.
- `gnn conformance (pinned)` (key `gnn-conformance`) — `./run.sh gnn`, which
  runs the shared `gnn.importers` reader over `specs/gnn-pin.json`,
  `.github/GNN.md` and `specs/coin_flip.gnn.md`, then validates the document
  against the parser pinned in `specs/gnn-pin.json` (currently v5.1.0, commit
  `75c834bd`): parser digests are verified before parsing, the pin's tag is
  resolved upstream and must name the pinned commit (`tag-commit-mismatch`),
  and the pin's language version must match the document and the parser.

Rules:

- `src/spec_reader.jl` must stay dependency free: the conformance job runs it
  with a bare `julia` binary and compares what it reads with the pinned GNN
  parser and the expectations in `scripts/validate_gnn_spec.py`.
- The conformance job installs Python and `uv` through
  `ActiveInferenceInstitute/.github/.github/actions/setup-python-uv@7159e67315330aac8e414aebae0ad1e999a41448`,
  and `./run.sh gnn` provisions the pinned revision (currently v5.1.0, commit
  `75c834bd8`) into `.gate/gnn-runtime`. It is a required check and must not be
  converted into a skip when the runtime cannot be provisioned; an unavailable
  runtime is exit `2`, never a pass.
- The test matrix runs `Pkg.test()`, which resolves dependencies from
  `Project.toml` because `Manifest.toml` is intentionally not committed. A
  failure on either matrix entry is a real failure; do not pin a version to
  hide it.
- Do not add a workflow step that repeats an arm's command. Add an arm to
  `run.sh`, document it in `docs/gate.md`, and call it from the job.
- Actions are pinned by commit. `dependabot.yml` groups `github-actions`
  updates, including the composite action above.
