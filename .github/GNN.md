# GNN conformance

`gnn conformance (pinned)` is the display name of the `gnn-conformance` job in
`.github/workflows/ci.yml`. It runs `./run.sh gnn`, the same arm a local run
executes, so the command exists in one place: `run.sh`.

The arm reads `specs/gnn-pin.json` (`gnn-importer-pin/v1`), which pins
`ActiveInferenceInstitute/Generalized_Notation_Notation` at `v5.1.0`
(`75c834bd8519dc7b5adc4d24f16bf393cfd1ecdf`), language version GNN v1.1,
with SHA-256 digests for the parser files under `src/gnn/`, including the shared
reader `src/gnn/importers.py`.

The job installs Python 3.12 and `uv` through
`ActiveInferenceInstitute/.github/.github/actions/setup-python-uv@7159e67315330aac8e414aebae0ad1e999a41448`,
sets up Julia, and runs `./run.sh gnn`. With no runtime in the environment the
arm installs the pinned commit into `.gate/gnn-runtime` with `uv`, then runs
three steps in that one environment:

1. `scripts/validate_gnn_spec.py --gnn-runtime … --julia julia --json` —
   verifies the installed parser file digests against the pin and checks the
   parsed model against the constants that script records: model name, variable
   dimensions, connection graph, scalar declarations, equation fragments,
   ontology annotations, required sections and a static time specification,
   plus the pinned semantic validator and consistency checker. Scalars are
   cross-read by the pinned parser, the script's own regular expressions and the
   Julia reader in `src/spec_reader.jl`, and the parser version must equal the
   pinned tag. This step runs first because step 2 imports the parser, and each
   subprocess of it runs with `-P` so the package whose digests are verified is
   the package the probe imports.
2. `python -P -m gnn.importers check --repo . --require-pointer --workflow
   .github/workflows/ci.yml --job gnn-conformance` — the estate's shared reader
   validates this pin, this pointer and `specs/coin_flip.gnn.md`.
3. The validator's offline unit tests, `test/test_validate_gnn_spec.py` and
   `test/test_gnn_verification_order.py`.

The arm parses only `specs/coin_flip.gnn.md`; a model added elsewhere is
invisible to the model-conformance step, and the shared reader's specification
check covers exactly the `*.gnn.md` files the repository carries.

The pin record is validated by that arm, not by the `lint` arm: `lint` checks
syntax only. A `Pkg.test()` run also reads the document, through the Julia
reader, but it never imports the pinned upstream parser.
