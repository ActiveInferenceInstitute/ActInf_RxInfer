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
- [`validate_gnn_spec.py`](validate_gnn_spec.py) — the GNN validation gate. It
  reads the pin from `specs/gnn-pin.json`, verifies the parser files, parses the
  document, and compares the result with what `src/spec_reader.jl` reads and
  with the expectations in the script.
- [`gnn_parser_probe.py`](gnn_parser_probe.py) — the only module that imports
  the upstream `gnn` package; the validator runs it as a subprocess against the
  pinned source tree.

Run through the entry point, which supplies the environment:

```sh
./run.sh lint
./run.sh docs
./run.sh gnn
```

The validator's runtime comes from `--gnn-runtime`/`GNN_RUNTIME_PYTHON`, from a
checkout via `--gnn-root`/`GNN_ROOT`, or from the runtime `./run.sh gnn`
provisions with `uv`. Without one the script exits `2` and says the check did
not run.
