# GNN conformance

`gnn conformance (pinned)` is the display name of the `gnn-conformance` job in
`.github/workflows/ci.yml`. It runs `./run.sh gnn`, the same arm a local run
executes, so the command exists in one place: `run.sh`.

The arm reads `specs/gnn-pin.json` (`gnn-importer-pin/v1`), which pins
`ActiveInferenceInstitute/Generalized_Notation_Notation` at `v5.0.3`
(`8f293d9ba810e6eda5c09842d9c7ed9ffa5f92c1`), language version GNN v1.1,
with SHA-256 digests for five parser files under `src/gnn/`.

The job installs Python 3.12 and `uv` through
`ActiveInferenceInstitute/.github/.github/actions/setup-python-uv@7159e67315330aac8e414aebae0ad1e999a41448`,
sets up Julia, and runs `./run.sh gnn`. With no runtime or checkout in the
environment the arm installs the pinned commit into `.gate/gnn-runtime` with
`uv`, then verifies the installed parser digests against the pin and runs
`scripts/validate_gnn_spec.py --gnn-runtime … --julia julia --json` on
`specs/coin_flip.gnn.md`. That script parses only `specs/coin_flip.gnn.md`,
through `scripts/gnn_parser_probe.py`, and compares it with the constants
it records: model name, variable dimensions, connection graph, scalar
declarations, equation fragments, ontology annotations, required sections
and a static time specification, plus the pinned semantic validator and
consistency checker. Scalars are cross-read by the pinned parser, the
script's own regular expressions and the Julia reader in
`src/spec_reader.jl`. It does not scan the rest of the repository for
`*.gnn.md`; a model added elsewhere is invisible to this job.

The pin record is validated by that arm, not by the `lint` arm: `lint` checks
syntax only. A `Pkg.test()` run also reads the document, through the Julia
reader, but it never imports the pinned upstream parser.
