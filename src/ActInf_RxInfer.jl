"""
    ActInf_RxInfer

Active Inference and RxInfer.jl.

The generative model of this package is the Beta-Bernoulli coin flip declared
in `specs/coin_flip.gnn.md` (Generalized Notation Notation, GNN). The document
is the single source of truth: [`spec_parameters`](@ref) reads the declared
prior, observation count, and seed from it, [`coin_model`](@ref) is the RxInfer
model, [`coin_data`](@ref) simulates observations, and
[`coin_posterior`](@ref) runs message passing while
[`analytic_posterior`](@ref) gives the closed-form conjugate posterior the
result is compared against. `examples/coin_flip.jl` runs the whole path.
"""
module ActInf_RxInfer

using Distributions
using Random
using RxInfer

include("spec_reader.jl")

export GNNSpecParameters, SPEC_PATH, spec_model_name, spec_parameters, spec_scalar
export spec_section, spec_summary
export analytic_posterior, coin_data, coin_model, coin_posterior

# The Beta-Bernoulli coin-flip model declared by `specs/coin_flip.gnn.md`: the
# coin bias follows `θ ~ Beta(a, b)` and the observations `y[i]` follow
# `Bernoulli(θ)`. The model documentation is attached after the definition
# because a leading docstring on `@model function` makes the GraphPPL macro
# expansion raise the "does not support positional arguments" error at load
# time (verified on Julia 1.13.3 with GraphPPL 4.9.0).
@model function coin_model(y, a, b)
    θ ~ Beta(a, b)
    for i in eachindex(y)
        y[i] ~ Bernoulli(θ)
    end
end

@doc """
    coin_model(y, a, b)

The model of `specs/coin_flip.gnn.md`. Supply `y` as data and `a`, `b` as the
prior concentrations; the interfaces are passed by name at the call site.
""" coin_model

"""
    coin_data(theta_true, n; rng = Random.default_rng()) -> Vector{Bool}

Simulate `n` independent coin tosses with bias `theta_true`.

Seed `rng` to reproduce a run: `examples/coin_flip.jl` seeds
`Random.default_rng()` with the `seed` declaration of the GNN document.
"""
function coin_data(theta_true::Real, n::Integer; rng::AbstractRNG = Random.default_rng())
    return rand(rng, Bernoulli(Float64(theta_true)), Int(n))
end

"""
    coin_posterior(y; a, b, kwargs...) -> Any

Run RxInfer message passing for [`coin_model`](@ref) on the observations `y`
and return the posterior over the coin bias. Remaining keywords are forwarded
to `RxInfer.infer`.

The returned object is distribution-like: `mean`, `std`, and `quantile` are the
supported summaries.
"""
function coin_posterior(y; a::Real, b::Real, kwargs...)
    result = infer(
        model = coin_model(a = Float64(a), b = Float64(b)),
        data = (y = y,),
        kwargs...,
    )
    return result.posteriors[:θ]
end

"""
    analytic_posterior(y; a, b) -> Beta

Return the closed-form conjugate posterior `Beta(a + k, b + n - k)` for `n`
observations with `k = sum(y)` successes, the target that message passing is
checked against.
"""
function analytic_posterior(y; a::Real, b::Real)
    successes = sum(y)
    return Beta(a + successes, b + length(y) - successes)
end

end
