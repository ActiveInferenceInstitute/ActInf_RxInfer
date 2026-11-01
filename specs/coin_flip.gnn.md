# GNN Specification: ActInf_RxInfer Beta-Bernoulli Coin Flip

## GNNSection

ActInfConjugate

## GNNVersionAndFlags

GNN v1.1

## ModelName

ActInf_RxInfer Beta-Bernoulli Coin Flip

## ModelAnnotation

Conjugate continuous generative model of a biased coin, implemented by
`src/ActInf_RxInfer.jl` and run by `examples/coin_flip.jl` in
ActInf_RxInfer.

- `theta` is the coin bias, drawn from the `Beta(a, b)` prior; the `n`
  observations `y_i ~ Bernoulli(theta)` are conditionally independent given
  `theta`.
- Message passing in RxInfer returns the exact conjugate posterior
  `Beta(a + k, b + n - k)` with the sufficient statistic `k = sum(y)`; the
  implementation checks the inferred posterior against that closed form.
- This is a conjugate exponential-family model. GNN's framework renderers
  target discrete POMDPs and linear-Gaussian state spaces, so this document is
  validated and read by tooling rather than rendered; the Julia code consumes
  the declared parameters directly through `spec_parameters`.

## StateSpaceBlock

theta[1,type=float]      # Latent coin bias, Beta(a, b)
y[500,1,type=int]        # Bernoulli observations
k[1,type=int]            # Sufficient statistic, number of successes
a[1,type=float]          # Prior concentration a
b[1,type=float]          # Prior concentration b

## Connections

a>theta
b>theta
theta>y
y>k

## InitialParameterization

a={(2.0)}
b={(2.0)}
theta_true={(0.75)}
n_observations={(500)}
seed={(123)}

## Equations

Prior and likelihood:

theta ~ Beta(a, b)
y_i | theta ~ Bernoulli(theta),  i = 1, ..., n

Sufficient statistic:

k = sum_{i=1}^{n} y_i

Exact conjugate posterior returned by message passing:

theta | y ~ Beta(a + k, b + n - k)

Reference values checked by the implementation:

mean(theta | y) = (a + k) / (a + b + n)
var(theta | y) = (a + k) (b + n - k) / ((a + b + n)^2 (a + b + n + 1))

## Time

Static

## ActInfOntologyAnnotation

theta=HiddenState
y=Observation
k=SufficientStatistic
a=PriorConcentrationA
b=PriorConcentrationB

## ModelParameters

model_family: beta_bernoulli
latent_variable: theta
observations: y
prior: beta
likelihood: bernoulli
posterior_family: beta
inference: conjugate_message_passing
n_observations: 500
prior_a: 2.0
prior_b: 2.0
theta_true: 0.75
seed: 123
posterior_mean: closed_form_conjugate_beta
implementation: src/ActInf_RxInfer.jl
example: examples/coin_flip.jl

## Footer

ActInf_RxInfer Beta-Bernoulli coin flip — canonical GNN fixture of
ActInf_RxInfer. Authored by hand as the single source of truth for the model.
Verified with the pinned upstream parser recorded in `specs/gnn-pin.json`.

## Signature

Not cryptographically signed.
