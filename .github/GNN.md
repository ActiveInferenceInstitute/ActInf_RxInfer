# GNN conformance

`gnn conformance (pinned)` is the display name of the `gnn-conformance` job in
`.github/workflows/ci.yml`. It runs `./run.sh gnn`, the same arm a local run
executes, so the command exists in one place: `run.sh`.

The arm reads `specs/gnn-pin.json` (`gnn-importer-pin/v1`), which pins
`ActiveInferenceInstitute/Generalized_Notation_Notation` at `v5.1.0`
(`75c834bd8519dc7b5adc4d24f16bf393cfd1ecdf`), language version GNN v1.1,
with SHA-256 digests for the parser files under `src/gnn/`, including the shared
reader `src/gnn/importers.py`.

The job retains its pinned shared Python/uv setup action and Julia setup, and
runs only `./run.sh gnn`. Its launch must additionally supply independently
reviewed `GNN_BOOTSTRAP` and `GNN_SOURCE_MANIFEST` files; no unchecked download
or private local artifact path is a hosted-resource contract.

The arm first runs model conformance: the reviewed producer normalizes the
unchanged pin, and a fresh selected-runtime probe performs parser and verdict
imports/calls inside source qualification through exit revalidation. Scalars
still agree across the pinned parser, local regex reader and Julia reader.
Next, the standalone producer's shared checker validates this pin, this
pointer and `specs/coin_flip.gnn.md` under its own guarded lifetime. Last,
regressions cover real producer-source/process admission and dispatch/cache
behavior.

Installed mode requires genuine matching Git PEP 610, distribution/module
ownership and complete content. Explicit source mode requires an explicit
runtime/package artifact and reports its narrower scope. Failed installed
admission never falls back to source. `run.sh` owns exact commands and tag selection.

The arm parses only `specs/coin_flip.gnn.md`; a model added elsewhere is
invisible to the model-conformance step, and the shared reader's specification
check covers exactly the `*.gnn.md` files the repository carries.

The pin record is validated by that arm, not by the `lint` arm: `lint` checks
syntax only. A `Pkg.test()` run also reads the document, through the Julia
reader, but it never imports the pinned upstream parser.
