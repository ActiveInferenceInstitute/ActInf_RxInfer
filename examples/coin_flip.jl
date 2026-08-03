# ActInf_RxInfer — coin-flip example
#
# Estimates the bias of a coin with a Beta-Bernoulli model using RxInfer.jl.
# This is the canonical "learn the bias of a coin" example from the RxInfer
# documentation (https://docs.rxinfer.com/stable/).
#
# Run from the repository root:
#
#     julia --project=. examples/coin_flip.jl
#
# Expected behaviour: the inferred posterior mean should be close to the true
# bias (0.75) given 500 observations, and the 95% credible interval should
# contain it.

using Distributions
using Random
using RxInfer

# Define the model: a Beta prior over the coin bias, with Bernoulli
# observations conditioned on the bias.
@model function coin_model(y, a, b)
    θ ~ Beta(a, b)
    for i in eachindex(y)
        y[i] ~ Bernoulli(θ)
    end
end

# Simulate 500 coin tosses with a fixed seed for reproducibility.
Random.seed!(123)
θ_real = 0.75
n = 500
y = rand(Bernoulli(θ_real), n)

# Run message-passing inference with a Beta(2, 2) prior.
result = infer(
    model = coin_model(a = 2.0, b = 2.0),
    data = (y = y,)
)

posterior = result.posteriors[:θ]

println("True bias:        ", θ_real)
println("Inferred mean:    ", mean(posterior))
println("Inferred std:     ", std(posterior))
println("95% CI:           ", quantile(posterior, [0.025, 0.975]))
