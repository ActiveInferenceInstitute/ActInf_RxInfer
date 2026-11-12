# GNN conformance

`gnn conformance (pinned)` is the `gnn-conformance` job in
`.github/workflows/ci.yml`. It reads `specs/gnn-pin.json`
(`gnn-importer-pin/v1`), which pins
`ActiveInferenceInstitute/Generalized_Notation_Notation` at `v5.0.3`
(`8f293d9ba810e6eda5c09842d9c7ed9ffa5f92c1`), language version GNN v1.1,
with SHA-256 digests for five parser files under `src/gnn/`.

The job installs that commit into a Python 3.12 `uv` runtime, verifies the
installed parser digests against the pin, and runs
`scripts/validate_gnn_spec.py --gnn-runtime ... --julia julia --json` on
`specs/coin_flip.gnn.md`. That script parses only `specs/coin_flip.gnn.md`,
through `scripts/gnn_parser_probe.py`, and compares it with the constants
it records: model name, variable dimensions, connection graph, scalar
declarations, equation fragments, ontology annotations, required sections
and a static time specification, plus the pinned semantic validator and
consistency checker. Scalars are cross-read by the pinned parser, the
script's own regular expressions and the Julia reader in
`src/spec_reader.jl`. It does not scan the rest of the repository for
`*.gnn.md`; a model added elsewhere is invisible to this job.
