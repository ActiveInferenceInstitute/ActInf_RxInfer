# `.github/workflows/`

[`ci.yml`](ci.yml) runs on pushes and pull requests to `main`, on manual
dispatch, and cancels a superseded run on the same ref.

| Job | What it proves |
|---|---|
| `test (julia 1.10)` and `test (julia 1)` | `Pkg.test()` on the long-term support release and on stable. |
| `gnn conformance (pinned)` | `specs/coin_flip.gnn.md` parses under the pinned parser and reads identically through `src/spec_reader.jl`. |

The conformance job installs the commit from `specs/gnn-pin.json` into its own
Python runtime and digest-verifies the parser files before use. It is required
and fails rather than skips when the runtime cannot be provisioned.
