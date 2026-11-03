# `specs/`

- [`coin_flip.gnn.md`](coin_flip.gnn.md) — the GNN declaration of the
  Beta-Bernoulli coin-flip model: prior concentrations, observation model,
  sufficient statistic, and the conjugate posterior. It is the single source of
  truth for the prior, observation count and seed.
- [`gnn-pin.json`](gnn-pin.json) — the upstream repository, tag `v5.0.3`, commit
  `8f293d9ba810e6eda5c09842d9c7ed9ffa5f92c1`, language version, and the SHA-256
  of each parser file.

Validate with [`../scripts/validate_gnn_spec.py`](../scripts/validate_gnn_spec.py);
the model is read by [`../src/spec_reader.jl`](../src/spec_reader.jl).
