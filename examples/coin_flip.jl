# ActInf_RxInfer — coin-flip example
#
# Estimates the bias of a coin with a Beta-Bernoulli model using RxInfer.jl.
# The model, and every number used below, is declared in the Generalized
# Notation Notation document specs/coin_flip.gnn.md and read from there. The
# posterior returned by message passing is compared against the closed-form
# conjugate posterior Beta(a + k, b + n - k).
#
# Run from the repository root:
#
#     julia --project=. examples/coin_flip.jl
#
# Expected behaviour: the inferred posterior matches the conjugate posterior,
# whose mean is close to the true bias (0.75) given 500 observations, and whose
# 95% credible interval contains it.

using ActInf_RxInfer
using Distributions
using Random

parameters = spec_parameters(SPEC_PATH)

# Simulate the declared number of tosses with the declared bias and seed.
Random.seed!(parameters.seed)
y = coin_data(parameters.theta_true, parameters.n_observations)

# Run message-passing inference under the declared prior.
posterior = coin_posterior(y; a = parameters.prior_a, b = parameters.prior_b)
reference = analytic_posterior(y; a = parameters.prior_a, b = parameters.prior_b)

println("Specification:    ", SPEC_PATH)
println("True bias:        ", parameters.theta_true)
println("Observations:     ", parameters.n_observations, " (", sum(y), " successes)")
println("Inferred mean:    ", mean(posterior))
println("Inferred std:     ", std(posterior))
println("95% CI:           ", quantile(posterior, [0.025, 0.975]))
println("Conjugate mean:   ", mean(reference))
println("Conjugate std:    ", std(reference))
