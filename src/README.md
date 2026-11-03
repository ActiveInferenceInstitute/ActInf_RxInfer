# `src/`

- [`ActInf_RxInfer.jl`](ActInf_RxInfer.jl) — the module. Exports
  `GNNSpecParameters`, `SPEC_PATH`, `spec_model_name`, `spec_parameters`,
  `spec_scalar`, `spec_section`, `spec_summary`, `analytic_posterior`,
  `coin_data`, `coin_model` and `coin_posterior`.
- [`spec_reader.jl`](spec_reader.jl) — the dependency-free reader for
  `specs/coin_flip.gnn.md`; it has no `using` statements.

Load with `julia --project=. -e 'using ActInf_RxInfer'`. The model declaration
is in [`../specs/coin_flip.gnn.md`](../specs/coin_flip.gnn.md).
