# Gate

`./run.sh` is the only gate entry point. Each arm runs one command, and the
workflow `.github/workflows/ci.yml` runs the same script, so no command is
written twice. The arms are independent: CI runs them in separate jobs, and a
local run can execute one arm at a time.

```sh
./run.sh            # default arm: lint, then fast
./run.sh all        # lint, full, docs, gnn
```

`./run.sh --help` prints the arm list and the environment variables. The
measurements for this host live in [the generated record](_generated/gate.md);
do not copy numbers from it into prose, and do not edit it by hand.

## Arms

| Arm | Command | What it proves | Needs |
| --- | --- | --- | --- |
| `lint` | `python3 scripts/lint.py` | Every tracked and untracked-but-not-ignored `.jl` file parses, every `.py` file compiles, every `.json` file is valid JSON, and every `.sh` file passes `bash -n` and carries the executable bit. | `julia`, `python3`, `bash` |
| `fast` | `ACTINF_RXINFER_TEST_ARM=fast julia --project=. --startup-file=no test/runtests.jl` | The declared GNN model, the reader's error paths, and reproducible data generation. The two testsets that start RxInfer message passing are reported as deferred. | `julia` with the project instantiated |
| `full` | `ACTINF_RXINFER_TEST_ARM=full julia --project=. --startup-file=no -e 'using Pkg; Pkg.test()'` | Every testset, through the package's `test` target, even when the caller exports `ACTINF_RXINFER_TEST_ARM=fast`. This is the command CI runs on both Julia versions. | `julia` |
| `docs` | `python3 scripts/check_links.py` then `python3 scripts/gate_report.py --check` | Relative Markdown links resolve, `#fragment` targets exist, `docs/index.md` links every documentation page, `docs/documentation-index.md` lists every long-lived page, and the generated measurement table matches its receipt. External URLs are not fetched. | `python3` |
| `gnn` | `./run.sh gnn` (sole implementation of model conformance, standalone producer checking and regressions) | Checked bootstrap and complete exact-pin manifest; guarded imports/verdicts and exit revalidation; genuine installed Git origin or explicitly labeled source artifact; tag binding and unchanged model/reader agreement | Selected parser runtime/dependencies, both reviewed resources, Julia reader, and prepared tag store or admitted remote lookup |
| `measure` | `python3 scripts/gate_report.py` | Times every arm once and rewrites `docs/_generated/gate.md` from `docs/_generated/gate-receipt.json`. | Everything the arms need |

There is no `types` arm: this is a Julia repository with no static type checker
and no formatter configured, so `test/runtests.jl` and `scripts/lint.py` are the
checked contract. Add a `types` arm only together with the checker it runs.

## The fast arm

The suite marks its two message-passing testsets as expensive. The `fast` arm
sets `ACTINF_RXINFER_TEST_ARM=fast`, and `test/runtests.jl` reports those
testsets as deferred instead of running them. The `full` arm explicitly sets
`ACTINF_RXINFER_TEST_ARM=full`, overriding an inherited `fast` value, so CI
runs everything. Direct test-suite invocation accepts `fast` and `full`
(the default); any other value is an error.

## GNN arm environments

Both GNN verdict steps use the same selected runtime and independently frozen
`GNN_BOOTSTRAP` and `GNN_SOURCE_MANIFEST` resources. The adapter checks the
bootstrap SHA-256 and compiles those exact bytes as a non-GNN module before
reading the pin or importing GNN. It binds the complete v5.1.0 manifest, not an
inventory inferred from the runtime.

Installed mode is the default: `GNN_RUNTIME_PYTHON` selects an existing
distribution, or `uv` provisions the pin from its canonical repository. Local
checkout provisioning through `GNN_ROOT` is rejected before cache access or
mutation. The producer requires distribution/module ownership, exact Git PEP 610
repository/commit and complete content; local Git URLs cannot satisfy that origin.
`GNN_ORIGIN_MODE=source` requires an explicit runtime and `GNN_PACKAGE_ROOT`
naming the deliberately selected `gnn` directory. Its receipt says
`explicit-source`, not installed VCS qualification. Failed installed admission
never falls back to source.

The model probe and producer checker keep actual imports and verdict calls
inside their qualified lifetime through exit revalidation. Missing resources
or unavailable runtime/admission exit `2` and report not run. Source/import
qualification is not scientific execution attestation. Hosted launches still
need independently admitted delivery of both reviewed resources.

The default gate checks the live upstream tag. For an offline run, prepare
a Git store while online by fetching the exact tag from the repository in
[the pin](../specs/gnn-pin.json). Keep its `origin` set to that repository.
Compare the fetched tag's peeled commit with the live upstream advertisement
and the pin before the offline run. Pass its absolute path as
`GNN_TAG_STORE=/path/to/prepared/store ./run.sh gnn` with the pinned runtime
available. The receipt identifies the local store as its source. A missing
tag, incorrect origin, or mismatched commit fails the gate.

## CI mapping

| Job key | Display name | Runs |
| --- | --- | --- |
| `test` | `test (julia <version>)` | `./run.sh full` on Julia 1.10 and on stable |
| `static` | `static (lint, docs)` | `./run.sh lint`, then `./run.sh docs` |
| `gnn-conformance` | `gnn conformance (pinned)` | `./run.sh gnn`, provisioned from the pin |

The `static` job uses the runner's `python3`; the `gnn` job installs Python and
`uv` through
`ActiveInferenceInstitute/.github/.github/actions/setup-python-uv@7159e67315330aac8e414aebae0ad1e999a41448`,
pinned by commit. GitHub Actions is billing-locked for this organization, so a
local `./run.sh all` is the gate that decides a change.

## Failure propagation

An arm fails if any command in it fails. The dispatcher runs an arm in a tested
context (`run_arm "$arm" || status=$?`), and Bash suppresses `set -e` for a
whole function in that context, so an arm must chain its subcommands explicitly
(`a && b`, or `provision || return $?`) instead of relying on errexit. A command
that succeeds after a failed one must never decide the arm's status: the `docs`
arm returns nonzero as soon as `scripts/check_links.py` fails, and `all` stops at
the first failing arm.

Provisioning invalidates the old success marker before mutating the runtime.
Creation, installation, marker staging and marker publication failures return
nonzero; none may leave a successful marker for a partially changed runtime.
A matching existing runtime is reused without reinstalling. A new marker is
published atomically only after provisioning succeeds.

`python3 -m unittest discover -s test -p test_run_gate.py` exercises these
dispatcher and cache transitions with controlled executables. It does not
qualify Julia inference or an installed GNN parser; use their real arms for that.

## Environment variables

| Variable | Used by | Meaning |
| --- | --- | --- |
| `JULIA_BIN` | all Julia arms, `gnn` | Julia interpreter (default `julia`) |
| `PYTHON` | `lint`, `docs`, `gnn`, `measure` | Python 3 interpreter (default `python3`) |
| `GNN_RUNTIME_PYTHON` | `gnn` | Selected parser interpreter; required explicitly in source mode |
| `GNN_TAG_STORE` | `gnn` | Prepared Git store holding the pinned tag, used instead of a live upstream lookup (offline run) |
| `GNN_BOOTSTRAP` | `gnn` | Independently reviewed bootstrap; fixed digest in `scripts/gnn_source.py` |
| `GNN_SOURCE_MANIFEST` | `gnn` | Independent complete v5.1.0 package manifest; fixed digest in the adapter |
| `GNN_ORIGIN_MODE` | `gnn` | `installed` (default) or explicitly selected `source`; never automatic fallback |
| `GNN_PACKAGE_ROOT` | `gnn` | Expected `gnn` directory; required in source mode |
| `ACTINF_GATE_DIR` | `gnn` | Where a provisioned runtime is cached (default `.gate`, ignored by Git) |
