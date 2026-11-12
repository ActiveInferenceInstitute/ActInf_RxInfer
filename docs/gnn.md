# Generalized Notation Notation

[Generalized Notation Notation](https://github.com/ActiveInferenceInstitute/Generalized_Notation_Notation)
(GNN) is a text format for declaring Active Inference generative models. The
Beta-Bernoulli coin-flip model this repository implements is declared as a GNN
document, so the prior, likelihood, sufficient statistic, and posterior are
readable outside the Julia code, and the Julia code is built from those
declarations.

## Files

* `specs/coin_flip.gnn.md` — the GNN document for the coin-flip model: latent
  bias `theta`, observations `y`, prior concentrations `a` and `b`, the
  sufficient statistic `k = sum(y)`, and the closed-form conjugate posterior
  `theta | y ~ Beta(a + k, b + n - k)`.
* `specs/gnn-pin.json` — the pin record: upstream repository, tag `v5.0.3`,
  commit `8f293d9ba810e6eda5c09842d9c7ed9ffa5f92c1`, and SHA-256 digests of the
  parser files that validate the document.
* `src/spec_reader.jl` — the dependency-free reader. `spec_parameters()` returns
  the declared prior, observation count, and seed; `examples/coin_flip.jl` and
  `test/runtests.jl` use it instead of repeating numbers in code.
* `scripts/validate_gnn_spec.py` and `scripts/gnn_parser_probe.py` — the
  pinned-parser validation described below.

The document is hand-authored and is the single source of truth for the model.
Changing the model means changing the document, the reader's expectations, and
the recorded example output together.

## Julia API

```julia
using ActInf_RxInfer

parameters = spec_parameters(SPEC_PATH)          # declared a, b, theta_true, n, seed
y = coin_data(parameters.theta_true, parameters.n_observations; rng = rng)
posterior = coin_posterior(y; a = parameters.prior_a, b = parameters.prior_b)
reference = analytic_posterior(y; a = parameters.prior_a, b = parameters.prior_b)
spec_model_name(SPEC_PATH)                        # "ActInf_RxInfer Beta-Bernoulli Coin Flip"
```

`spec_section`, `spec_scalar`, `spec_model_name`, `spec_parameters`, and
`spec_summary` live in `src/spec_reader.jl`, which has no `using` statements so
that a bare Julia binary can read the document. `spec_summary` prints
`key=value` lines; `scripts/validate_gnn_spec.py` compares them with the pinned
parser's view of the same document.

## Commands

```bash
# Julia test suite (reads the committed document)
julia --project=. -e 'using Pkg; Pkg.test()'

# Validate with the pinned upstream parser from a GNN checkout
GNN_ROOT=/path/to/Generalized_Notation_Notation \
GNN_PYTHON=/path/to/parser-runtime/bin/python \
python3 scripts/validate_gnn_spec.py --julia julia --json

# Installed pinned runtime (what CI uses)
python3 scripts/validate_gnn_spec.py \
  --gnn-runtime /path/to/venv/bin/python --julia julia --json
```

`GNN_ROOT` is a `Generalized_Notation_Notation` checkout: the validator resolves
the pinned commit with `git archive`, verifies every recorded parser digest, and
runs the parser from that materialized tree, so a live working copy under
development is never imported. `GNN_PYTHON` (or `--gnn-runtime`) selects the
interpreter that has the parser dependencies; the GNN checkout's own `.venv`
works. `--julia`/`JULIA_BIN` adds the cross-language reader check.

Exit codes are `0` pass, `1` conformance failure, and `2` pinned runtime, pinned
checkout, or requested Julia reader unavailable — an unavailable run is reported
as not run, never as a pass.

## What the validation checks

1. The pin: the resolved commit equals `specs/gnn-pin.json`, every recorded
   parser file digest matches **before the document is parsed**, and the pin's
   `tag` resolves to its `commit` in the GNN object store (a checkout's local
   tags, or `--verify-tag-remote` for `git ls-remote`). A tag that resolves
   elsewhere is a named `tag-commit-mismatch` failure; no object store is
   reported as unresolvable, never assumed.
2. The document parses with the pinned `gnn` parser with no errors or warnings,
   the distribution version equals the pinned tag, and the pin's
   `language_version` equals both the document's `GNNVersionAndFlags`
   declaration and the language version the parser reports. Disagreement is a
   named `language-version-mismatch` failure. For an installed runtime the
   installer's recorded VCS commit is compared with the pin when it exists;
   an install without that metadata is reported as unresolvable.
3. The declared model name, `StateSpaceBlock` variables and dimensions, the
   connection graph, the `InitialParameterization` scalars, the ontology
   annotations, and the section list match the expectations in
   `scripts/validate_gnn_spec.py`, and the equation section states the conjugate
   posterior `theta | y ~ Beta(a + k, b + n - k)`.
4. The declared scalars are read three ways — the pinned parser, the Python
   reader, and `src/spec_reader.jl` — and must agree.
5. The pinned semantic validator accepts the document and the consistency
   checker reports it as consistent.

The receipt is written to `docs/_build/gnn/validation-receipt.json`
(`--receipt` overrides it).

## Scope

The document covers the conjugate Beta-Bernoulli model of
`examples/coin_flip.jl` and the observations, prior, seed, and summary
statistics the repository verifies. GNN's framework renderers target discrete
POMDPs and linear-Gaussian state spaces; this conjugate model is not rendered
to another framework here, and no renderer output is claimed. The document is
validated and consumed directly.

## Related work

[GNN](https://github.com/ActiveInferenceInstitute/Generalized_Notation_Notation)
owns the notation, the parser, and the renderers, including its RxInfer.jl
backend; the
[framework integration guide](https://github.com/ActiveInferenceInstitute/Generalized_Notation_Notation/blob/main/docs/gnn/integration/framework_integration_guide.md)
documents the render and execute pipeline, and
[`docs/gnn/implementations/rxinfer.md`](https://github.com/ActiveInferenceInstitute/Generalized_Notation_Notation/blob/main/docs/gnn/implementations/rxinfer.md)
describes the RxInfer.jl target.
[ActiveBlockference](https://github.com/ActiveInferenceInstitute/ActiveBlockference)
applies the same pattern to a discrete grid-world POMDP, and
[ActiveInferenceImplementations](https://github.com/ActiveInferenceInstitute/ActiveInferenceImplementations)
collects RxInfer.jl notebooks including the same Beta-Bernoulli coin flip.
