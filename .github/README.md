# `.github/`

- [`dependabot.yml`](dependabot.yml) — dependency update configuration.
- [`workflows/ci.yml`](workflows/ci.yml) — the Julia test matrix, the static
  checks, and the required GNN conformance job. Every job runs `./run.sh`.
- [`GNN.md`](GNN.md) — what the conformance job parses, and the pin it uses.

Jobs:

| Key | Display name | Runs |
| --- | --- | --- |
| `test` | `test (julia <version>)` | `./run.sh full` on Julia 1.10 and stable |
| `static` | `static (lint, docs)` | `./run.sh lint`, `./run.sh docs` |
| `gnn-conformance` | `gnn conformance (pinned)` | `./run.sh gnn` |

The arms, their environments, and the measured wall times are documented in
[`../docs/gate.md`](../docs/gate.md) and
[`../docs/_generated/gate.md`](../docs/_generated/gate.md). CI rules are in
[`AGENTS.md`](AGENTS.md); repository gates are in
[`../AGENTS.md`](../AGENTS.md).
