# `specs/`

- [`coin_flip.gnn.md`](coin_flip.gnn.md) — the GNN declaration of the
  Beta-Bernoulli coin-flip model: prior concentrations, observation model,
  sufficient statistic, and the conjugate posterior. It is the single source of
  truth for the prior, observation count and seed.
- [`gnn-pin.json`](gnn-pin.json) — the upstream repository, tag `v5.1.0`, commit
  `75c834bd8519dc7b5adc4d24f16bf393cfd1ecdf`, language version, and the SHA-256
  of each parser file, including the shared `src/gnn/importers.py` reader.

The pin is read by `gnn.importers` from that pinned revision and the model is
checked by [`../scripts/validate_gnn_spec.py`](../scripts/validate_gnn_spec.py);
the model is read by [`../src/spec_reader.jl`](../src/spec_reader.jl).
