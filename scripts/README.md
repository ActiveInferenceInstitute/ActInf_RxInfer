# `scripts/`

- [`validate_gnn_spec.py`](validate_gnn_spec.py) — the GNN validation gate. It
  reads the pin from `specs/gnn-pin.json`, verifies the parser files **before**
  parsing, binds the pin's tag to its commit where an object store is
  available, checks the pin's declared language version against the document
  and the parser, parses the document, and compares the result with what
  `src/spec_reader.jl` reads and with the expectations in the script.
- [`gnn_parser_probe.py`](gnn_parser_probe.py) — the only module that imports
  the upstream `gnn` package; the validator runs it as a subprocess against the
  pinned source tree.

Run:

```sh
python3 scripts/validate_gnn_spec.py --gnn-runtime <python> --julia julia --json
```

The runtime comes from `--gnn-runtime`/`GNN_RUNTIME_PYTHON` or a checkout from
`--gnn-root`/`GNN_ROOT`. Without one the script exits `2` and says the check did
not run.
