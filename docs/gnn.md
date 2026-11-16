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

# Explicit source admission (not installed-origin qualification)
GNN_ORIGIN_MODE=source GNN_PACKAGE_ROOT=/path/to/gnn \
    GNN_RUNTIME_PYTHON=/path/to/venv/bin/python ./run.sh gnn
```

Use `./run.sh gnn`; the arm commands have no second implementation here.
First, the validator asks the independently checked standalone producer to
normalize the unchanged pin, then runs the self-guarding parser probe in the
selected runtime. Parsing, semantic validation, orientation and consistency
calls stay inside `qualified_source`; JSON is published only after exit
revalidation. The parent compares data with the unchanged model expectations
and the Julia reader. Second, the producer's shared `check_importer` validates
the pin, pointer and specifications under its own guarded lifetime. Last, the
arm runs regressions with the same selected runtime.

All launches require reviewed `GNN_BOOTSTRAP` and independently frozen complete
`GNN_SOURCE_MANIFEST` inputs. Their SHA-256 identities are fixed in
`scripts/gnn_source.py`; callers cannot bless target-derived manifests. The
unchanged v5.1.0 pin and every recorded parser digest remain required. Installed
mode also requires genuine matching Git PEP 610 and distribution/module
ownership; absent provenance refuses rather than permitting unresolved evidence.
Explicit source mode requires `GNN_ORIGIN_MODE=source`, an explicitly selected
runtime and `GNN_PACKAGE_ROOT`, and reports `explicit-source` without installed
VCS qualification.

`GNN_RUNTIME_PYTHON` selects the target interpreter; `--gnn-runtime` overrides
its environment default for direct validator use. Installed mode alone retains
the optional `uv` provisioning path from the canonical pinned repository.
Local-checkout provisioning through `GNN_ROOT` is rejected before cache access
or mutation: its genuine local Git PEP 610 URL cannot establish canonical
repository provenance. A previously local-provisioned cache is not relabelled;
select a fresh `ACTINF_GATE_DIR` for canonical provisioning, or an explicitly
qualified existing runtime. Missing runtimes and failed installed admission
never fall back to a checkout. `-P` excludes implicit cwd/script candidates;
source mode deliberately binds its named package root.

The gate uses a live tag check or an explicitly prepared `GNN_TAG_STORE` whose
single upstream origin and peeled tag match the pin. A missing tag, incorrect
origin or mismatched commit fails. Direct validator use without a tag option
records `tag_binding.status=unresolvable-offline`, not upstream tag verification.
See [`gate.md`](gate.md) for offline/cache rules and required launch inputs.

Exit codes are `0` pass, `1` conformance failure, and `2` pinned runtime,
requested Julia reader, or requested remote tag resolution unavailable — an unavailable run is reported as not run,
never as a pass.

## In CI

The check is the `gnn-conformance` job, displayed as `gnn conformance (pinned)`,
in [`.github/workflows/ci.yml`](../.github/workflows/ci.yml). The job installs
Python 3.12 and `uv` through
`ActiveInferenceInstitute/.github/.github/actions/setup-python-uv@7159e67315330aac8e414aebae0ad1e999a41448`
(pinned by commit), sets up Julia, and runs `./run.sh gnn`. The launch must
separately supply both reviewed resource files; local source-mode acceptance
does not establish hosted delivery. Missing resources or runtime fail, not skip.
What the job parses, and what it deliberately does not scan, is recorded in
[`.github/GNN.md`](../.github/GNN.md).

## What the validation checks

1. The standalone producer accepts `specs/gnn-pin.json` as a
   `gnn-importer-pin/v1` record naming the exact upstream release. Its complete
   package manifest and every pin-declared parser digest match the selected source.
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
`tag_binding`, `revision` and `source_qualification`. Installed revision is
verified only for admitted `installed-vcs` origin; source mode is explicitly
labeled. The receipt is written to `docs/_build/gnn/validation-receipt.json`
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

- The unchanged v5.1.0 pin and parser digests remain required. The independently
  checked standalone producer owns pin normalization and shared checking; no
  consumer pin parser was restored.
- The validator retains member-specific model/reader comparisons and consumes
  exit-qualified JSON from selected-runtime children. Obsolete local
  digest/revision admission programs were removed, not kept as fallbacks.
- `run.sh` remains the sole arm implementation. Model conformance precedes the
  standalone producer checker; each real GNN verdict has its own qualified lifetime.
- Canonical installed provisioning rejects `GNN_ROOT` before cache mutation.
  Explicit source admission uses `GNN_ORIGIN_MODE=source` and `GNN_PACKAGE_ROOT`,
  never an implicit fallback.
- `.github/GNN.md` retains the pin, revision, workflow and job identifiers.
  Historical migration and gate receipts retain their original bindings.

## Bootstrap admission boundary

The adapter checks bootstrap SHA-256
`f638d4c01fe7de31e43d793e59bf382d0c3d1a82f365c59238334a2b40adfb37`
and executes those same bytes under a non-GNN identity. It binds complete
v5.1.0 manifest SHA-256
`43b33c0b2b40386afa3f306fec4cc13bc1fd7c3b570fbf11d5008bad5c8e6b51`
before target imports. The producer guards real parser/checker work and
revalidates package content, module ownership and origin at exit; the adapter
also rechecks the independent resources.

Governed local real-source/process regressions exercise this boundary and the
unchanged model comparisons in explicit source mode. Installed distribution
provenance, full tag/Julia GNN-arm execution and hosted delivery remain separate
qualification obligations. Neither source admission nor historical receipts
attest new scientific results, dependency trust, publisher safety or hostile
filesystem isolation. Do not change the model or pin merely to obtain a pass.

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
