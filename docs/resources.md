# Resources

## RxInfer ecosystem

- [RxInfer.jl](https://github.com/ReactiveBayes/RxInfer.jl) — the upstream probabilistic programming and message-passing package.
- [RxInfer documentation](https://docs.rxinfer.com/) — stable and development documentation for RxInfer.jl.
- [RxInfer examples](https://examples.rxinfer.com/) — runnable upstream examples.
- [ReactiveMP.jl](https://github.com/ReactiveBayes/ReactiveMP.jl) — a declared dependency used by the RxInfer ecosystem.
- [RxInfer JOSS article](https://doi.org/10.21105/joss.05161) — the published software description.

## Active Inference

- [Active Inference Institute](https://www.activeinference.org/) — institute website.
- [Active Inference Ontology](https://github.com/ActiveInferenceInstitute/Active_Inference_Ontology) — related terminology and ontology work.
- [Factor graph](https://en.wikipedia.org/wiki/Factor_graph) — general background relevant to message-passing models.

## Generative-model specification

- [Generalized Notation Notation](https://github.com/ActiveInferenceInstitute/Generalized_Notation_Notation) (GNN) — the notation, parser, and renderers used for the `specs/coin_flip.gnn.md` declaration in this repository.
- [GNN framework integration guide](https://github.com/ActiveInferenceInstitute/Generalized_Notation_Notation/blob/main/docs/gnn/integration/framework_integration_guide.md) — render and execute pipeline, including the RxInfer.jl backend.
- [GNN RxInfer.jl implementation notes](https://github.com/ActiveInferenceInstitute/Generalized_Notation_Notation/blob/main/docs/gnn/implementations/rxinfer.md) — what the RxInfer.jl renderer supports.
- [ActiveBlockference](https://github.com/ActiveInferenceInstitute/ActiveBlockference) — a fleet repository applying the same GNN pattern to a discrete grid-world POMDP.
- [ActiveInferenceImplementations](https://github.com/ActiveInferenceInstitute/ActiveInferenceImplementations) — RxInfer.jl notebooks, including the same Beta–Bernoulli coin flip.

The repository is federated with broader InstituteOS metadata through its `.aii` sidecar. The sidecar is kept as repository metadata; no unavailable internal or private repository URL is used here.
