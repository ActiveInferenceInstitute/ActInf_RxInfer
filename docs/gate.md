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
| `gnn` | `python3 scripts/validate_gnn_spec.py --gnn-runtime … --julia julia --json` | The pin, the parser digests, the parsed model, and agreement between the pinned parser, the script's own reader, and `src/spec_reader.jl`. | A pinned GNN runtime or checkout; see [GNN](gnn.md) |
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

`./run.sh gnn` resolves the pinned parser in this order:

1. `GNN_RUNTIME_PYTHON` (or `--gnn-runtime`), an interpreter with the pinned
   distribution installed;
2. `GNN_ROOT` plus `GNN_PYTHON`, a `Generalized_Notation_Notation` checkout from
   which the pinned commit is materialized with `git archive`;
3. otherwise it provisions `specs/gnn-pin.json` into `.gate/gnn-runtime` with
   `uv`, which is what CI does.

A run that cannot resolve a runtime exits `2` and reports the check as not run.
It is never reported as a pass.

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

## Environment variables

| Variable | Used by | Meaning |
| --- | --- | --- |
| `JULIA_BIN` | all Julia arms, `gnn` | Julia interpreter (default `julia`) |
| `PYTHON` | `lint`, `docs`, `gnn`, `measure` | Python 3 interpreter (default `python3`) |
| `GNN_RUNTIME_PYTHON` | `gnn` | Already-installed pinned runtime |
| `GNN_ROOT`, `GNN_PYTHON` | `gnn` | Checkout of the pinned repository and its parser interpreter |
| `ACTINF_GATE_DIR` | `gnn` | Where a provisioned runtime is cached (default `.gate`, ignored by Git) |
