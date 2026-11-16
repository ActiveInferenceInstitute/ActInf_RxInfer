# `scripts/`

Gate arms and the GNN validation. Every script here is called by
[`../run.sh`](../run.sh); the arms and their environments are documented in
[`../docs/gate.md`](../docs/gate.md).

- [`lint.py`](lint.py) — the `lint` arm. Parses every tracked `.jl` file (a
  `:incomplete` or `:error` node fails), compiles every `.py` file, loads every
  `.json` file, and checks every `.sh` file with `bash -n` plus the executable
  bit. No third-party imports, nothing rewritten.
- [`check_links.py`](check_links.py) — the first half of the `docs` arm.
  Validates relative Markdown links and `#fragment` anchors offline, and
  requires `docs/index.md` to link every documentation page and
  `docs/documentation-index.md` to list every long-lived one.
- [`gate_report.py`](gate_report.py) — the `measure` arm and the second half of
  `docs`. It times each arm once, writes `docs/_generated/gate-receipt.json`,
  renders `docs/_generated/gate.md` from it, and with `--check` fails when the
  committed table disagrees with the receipt.
- [`gnn_source.py`](gnn_source.py) — binds the independently reviewed bootstrap
  and complete v5.1.0 manifest. It executes the same checked bytes as a non-GNN
  module and delegates pin normalization, source/origin admission and checking
  to the producer; it is not a second validator.
- [`validate_gnn_spec.py`](validate_gnn_spec.py) — orchestrates checked pin and
  guarded parser-probe children in the selected runtime, then compares JSON
  with unchanged model expectations. Tag/store, language-version and optional
  Julia-reader checks remain.
- [`gnn_parser_probe.py`](gnn_parser_probe.py) — imports no GNN at consumer
  module load. Direct Python and CLI entries keep real GNN imports and verdict
  calls inside the producer lifetime and publish only exit-revalidated JSON.

Run through the entry point, which supplies the environment:

```sh
./run.sh lint
./run.sh docs
./run.sh gnn
```

`--gnn-runtime`/`GNN_RUNTIME_PYTHON` selects the target interpreter. Both
independent resources are required. Installed mode requires genuine matching
distribution/PEP 610/full-content admission; explicit source mode requires a
named package artifact and runtime. Missing resources/runtime/admission exit
`2`. Local-checkout provisioning through `GNN_ROOT` is rejected before cache
mutation; explicit source admission uses `GNN_PACKAGE_ROOT`, never a fallback.
