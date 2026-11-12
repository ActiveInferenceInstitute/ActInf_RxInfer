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
* `specs/gnn-pin.json` — the pin record (`gnn-importer-pin/v1`): upstream
  repository, tag `v5.1.0`, commit `75c834bd8519dc7b5adc4d24f16bf393cfd1ecdf`,
  language version, and SHA-256 digests of the parser files that validate the
  document, including the shared reader `src/gnn/importers.py`.
* `.github/GNN.md` — the pointer that records what the conformance job parses
  and what it deliberately does not scan.
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
# The gate arm: resolves a runtime, checks the pin and the document
./run.sh gnn

# Installed pinned runtime
GNN_RUNTIME_PYTHON=/path/to/venv/bin/python ./run.sh gnn

# Provision from a local checkout instead of the pinned repository
GNN_ROOT=/path/to/Generalized_Notation_Notation ./run.sh gnn
```

`./run.sh gnn` runs three commands in one environment. First the validator:

```bash
python3 scripts/validate_gnn_spec.py --gnn-runtime <runtime>/bin/python \
    --julia julia --verify-tag-remote --json
```

which reads the pin through `gnn.importers.read_pin` in that runtime,
locates the installed package without importing it, verifies every recorded
parser digest against it *before* the document is parsed, compares the
installer's recorded VCS commit (`direct_url.json`) with the pin, and runs the
model-conformance checks below. It runs first because the second command
imports the parser and validates the document with it: nothing in the pinned
package is imported for that before the digests are checked. Every subprocess
the validator starts that imports the package runs with `-P`, so the working
directory and `scripts/` stay off `sys.path` and the package whose digests are
verified is the package the probe imports. `--julia`/`JULIA_BIN` adds the
cross-language reader check. `--verify-tag-remote` resolves the pin's `tag`
upstream with `git ls-remote` (the peeled commit of an annotated tag) and fails
as `tag-commit-mismatch` when it names a different commit than the pin; it needs
network access, and a remote that cannot answer ends the run as *not run*
(exit `2`). Without the flag nothing is resolved upstream and the receipt
records `tag_binding.status` as `unresolvable-offline`; likewise an install
without a recorded VCS commit is `unresolvable-offline` under `revision`, never
a pass. Second, the estate's shared reader:

```bash
python -P -m gnn.importers check --repo . --require-pointer \
    --workflow .github/workflows/ci.yml --job gnn-conformance
```

That reader is `src/gnn/importers.py` from the pinned revision; it reads
`specs/gnn-pin.json`, requires `.github/GNN.md` to name the pin, the revision,
the workflow and the job key, and validates `specs/coin_flip.gnn.md` with the
pinned parser. This repository keeps no second copy of that logic. Last,
`./run.sh gnn` runs the offline unit tests in
`test/test_validate_gnn_spec.py` and `test/test_gnn_verification_order.py`
(standard library, no network).

The runtime is `GNN_RUNTIME_PYTHON` when it is set; otherwise the arm installs
the pinned commit into `.gate/gnn-runtime` with `uv` (the path CI takes) and
caches it there by commit. `GNN_ROOT` names a `Generalized_Notation_Notation`
checkout to install that commit from instead of the pinned repository, so a live
working copy under development is never imported.

Exit codes are `0` pass, `1` conformance failure, and `2` pinned runtime,
requested Julia reader, or requested remote tag resolution unavailable — an unavailable run is reported as not run,
never as a pass.

## In CI

The check is the `gnn-conformance` job, displayed as `gnn conformance (pinned)`,
in [`.github/workflows/ci.yml`](../.github/workflows/ci.yml). The job installs
Python 3.12 and `uv` through
`ActiveInferenceInstitute/.github/.github/actions/setup-python-uv@7159e67315330aac8e414aebae0ad1e999a41448`
(pinned by commit), sets up Julia, and runs `./run.sh gnn`, which provisions the
pin and performs the validation. The job is a required check and is never
converted into a skip when the runtime cannot be provisioned. What the job
parses, and what it deliberately does not scan, is recorded in
[`.github/GNN.md`](../.github/GNN.md).

## What the validation checks

1. The pin: `gnn.importers` accepts `specs/gnn-pin.json` as a
   `gnn-importer-pin/v1` record that names the upstream repository, and every
   parser file digest it records matches the installed package.
2. The document parses with the pinned `gnn` parser with no errors or warnings,
   and the parser version equals the pinned tag. The parser is imported from the
   digest-verified package, the pin's `language_version` equals both the
   document's `GNNVersionAndFlags` and the parser's reported version
   (`language-version-mismatch`), and the pin's tag resolves to the pinned
   commit (`tag-commit-mismatch`, with `--verify-tag-remote`).
3. The declared model name, `StateSpaceBlock` variables and dimensions, the
   connection graph, the `InitialParameterization` scalars, the ontology
   annotations, and the section list match the expectations in
   `scripts/validate_gnn_spec.py`, and the equation section states the conjugate
   posterior `theta | y ~ Beta(a + k, b + n - k)`.
4. The declared scalars are read three ways — the pinned parser, the Python
   reader, and `src/spec_reader.jl` — and must agree.
5. The pinned semantic validator accepts the document and the consistency
   checker reports it as consistent.

The receipt also records `language_version`, `parser_language_version`,
`tag_binding` and `revision`. It is written to `docs/_build/gnn/validation-receipt.json`
(`--receipt` overrides it).

## GNN–FEP migration: adopted

The [GNN–FEP workflow contract](https://github.com/ActiveInferenceInstitute/Generalized_Notation_Notation/blob/main/docs/workflows/gnn-fep.md)
puts pin reading, pin and pointer validation, and specification validation in
one place — `src/gnn/importers.py` upstream — and asks each consumer to call it
from the environment containing its pin, never to carry a copy.

This repository's pin moved from `v5.0.3`
(`8f293d9ba810e6eda5c09842d9c7ed9ffa5f92c1`) to `v5.1.0`
(`75c834bd8519dc7b5adc4d24f16bf393cfd1ecdf`). The old revision predates the
reader and could not import it; `v5.1.0` contains `src/gnn/importers.py`, so
the cutover happened in the same change that advanced the pin:

- `scripts/validate_gnn_spec.py` no longer parses the pin's shape. It reads the
  pin with `gnn.importers.read_pin` in the pinned runtime and keeps only the
  checks that are this member's own: the parser digests, the parsed model, and
  the agreement of the pinned parser, the script's reader and
  `src/spec_reader.jl`.
- The pin-shape unit tests (`test/test_gnn_pin.py`) are gone. The shared reader
  reports `pin-*`, `spec-*` and `pointer-*` findings for those shapes.
- `./run.sh gnn` calls `python -P -m gnn.importers check --repo .
  --require-pointer --workflow .github/workflows/ci.yml --job gnn-conformance`
  in the runtime it builds, after the model-conformance step: that reader
  imports the pinned parser, so the digest verification runs first.
- The `git archive` materialization path (`--gnn-root`, `GNN_PYTHON`) is gone
  with the second reader. `GNN_ROOT` now names the checkout the pinned runtime
  is installed from, so both steps of the arm run in one installed revision.
- `.github/GNN.md` names the pin, the new revision, the workflow and the job
  key, which is what makes `--require-pointer` a pass.

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
