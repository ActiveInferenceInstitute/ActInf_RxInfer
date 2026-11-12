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
| `full` | `julia --project=. --startup-file=no -e 'using Pkg; Pkg.test()'` | Every testset, through the package's `test` target exactly as a user runs it. This is the command CI runs on both Julia versions. | `julia` |
| `docs` | `python3 scripts/check_links.py` then `python3 scripts/gate_report.py --check` | Relative Markdown links resolve, `#fragment` targets exist, `docs/index.md` links every documentation page, `docs/documentation-index.md` lists every long-lived page, and the generated measurement table matches its receipt. External URLs are not fetched. | `python3` |
| `gnn` | `python3 scripts/validate_gnn_spec.py --gnn-runtime … --julia julia --verify-tag-remote --json`, then `python -P -m gnn.importers check --repo . --require-pointer --workflow .github/workflows/ci.yml --job gnn-conformance`, then the offline validator unit tests (`test/test_validate_gnn_spec.py`, `test/test_gnn_verification_order.py`) | The installed parser digests match the pin (verified before anything imports the parser) and the pin's tag resolves to its commit; the shared reader then accepts the pin, the pointer and the document; the parsed model, the script's own reader, and `src/spec_reader.jl` agree. | A pinned GNN runtime, provisioned with `uv` when none is supplied; see [GNN](gnn.md) |
| `measure` | `python3 scripts/gate_report.py` | Times every arm once and rewrites `docs/_generated/gate.md` from `docs/_generated/gate-receipt.json`. | Everything the arms need |

There is no `types` arm: this is a Julia repository with no static type checker
and no formatter configured, so `test/runtests.jl` and `scripts/lint.py` are the
checked contract. Add a `types` arm only together with the checker it runs.

## The fast arm

The suite marks its two message-passing testsets as expensive. The `fast` arm
sets `ACTINF_RXINFER_TEST_ARM=fast`, and `test/runtests.jl` reports those
testsets as deferred instead of running them; the `full` arm, and therefore CI,
runs everything. `ACTINF_RXINFER_TEST_ARM` accepts `fast` and `full` (the
default) and any other value is an error.

## GNN arm environments

`./run.sh gnn` runs in one environment, and both of its commands use it:

1. `GNN_RUNTIME_PYTHON`, an interpreter with the pinned distribution installed;
2. otherwise the pinned revision installed into `.gate/gnn-runtime` with `uv`,
   which is what CI does. `GNN_ROOT` names a `Generalized_Notation_Notation`
   checkout to install that commit from instead of the pinned repository.

That interpreter first runs `scripts/validate_gnn_spec.py --gnn-runtime …`,
which verifies the installed parser digests, and then `python -P -m
gnn.importers check --repo . --require-pointer --workflow
.github/workflows/ci.yml --job gnn-conformance`, which is the command that
imports that parser and validates the document with it. The order is the
point: nothing in the pinned package is imported by the arm before the digests
recorded in the pin have been checked. A run that cannot resolve the runtime
exits `2` and reports the check as not run. It is never reported as a pass.

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

## Environment variables

| Variable | Used by | Meaning |
| --- | --- | --- |
| `JULIA_BIN` | all Julia arms, `gnn` | Julia interpreter (default `julia`) |
| `PYTHON` | `lint`, `docs`, `gnn`, `measure` | Python 3 interpreter (default `python3`) |
| `GNN_RUNTIME_PYTHON` | `gnn` | Already-installed pinned runtime |
| `GNN_ROOT` | `gnn` | Checkout to install the pinned revision from, instead of the pinned repository |
| `ACTINF_GATE_DIR` | `gnn` | Where a provisioned runtime is cached (default `.gate`, ignored by Git) |
