# `.github/workflows/`

[`ci.yml`](ci.yml) runs on pushes and pull requests to `main`, on manual
dispatch, and cancels a superseded run on the same ref. Every job runs an arm of
[`../../run.sh`](../../run.sh); the workflow holds no command of its own.

| Job | Key | Runs |
|---|---|---|
| `test (julia 1.10)`, `test (julia 1)` | `test` | `./run.sh full` — `Pkg.test()` on the long-term support release and on stable |
| `static (lint, docs)` | `static` | `./run.sh lint`, then `./run.sh docs` |
| `gnn conformance (pinned)` | `gnn-conformance` | `./run.sh gnn` — the document parses under the pinned parser and reads identically through `src/spec_reader.jl` |

The conformance job installs Python 3.12 and `uv` through
`ActiveInferenceInstitute/.github/.github/actions/setup-python-uv@7159e67315330aac8e414aebae0ad1e999a41448`,
then `./run.sh gnn` provisions the commit from `specs/gnn-pin.json` into
`.gate/gnn-runtime` and digest-verifies the parser files before use. It is
required and fails (exit `2`, "not run") rather than skips when the runtime
cannot be provisioned.

Arms, environments, and the measured wall times are documented in
[`../../docs/gate.md`](../../docs/gate.md) and
[`../../docs/_generated/gate.md`](../../docs/_generated/gate.md).
