# `examples/`

[`coin_flip.jl`](coin_flip.jl) estimates a coin's bias with a Beta-Bernoulli
model in RxInfer.jl and compares the message-passing posterior with the
closed-form conjugate posterior. Every number comes from
[`../specs/coin_flip.gnn.md`](../specs/coin_flip.gnn.md) through
`spec_parameters`.

Run from the repository root:

```sh
julia --project=. examples/coin_flip.jl
```
