#!/usr/bin/env bash
# The repository gate. Every arm runs one command and CI runs this script, so
# there is no second copy of any command. Documentation: docs/gate.md.
#
# usage:begin
#   ./run.sh                default arm: lint, then the fast tests
#   ./run.sh lint           syntax checks: Julia parse, Python AST, JSON, shell
#   ./run.sh fast           the test suite without RxInfer message passing
#   ./run.sh full           the test suite through `Pkg.test()` (what CI runs)
#   ./run.sh docs           relative links, the docs hub, generated numbers
#   ./run.sh gnn            the pinned GNN conformance check
#   ./run.sh measure        time every arm and refresh docs/_generated/gate.md
#   ./run.sh all            lint, full, docs, gnn (the arms a release needs)
#
# Environment:
#   JULIA_BIN              Julia interpreter (default: julia)
#   PYTHON                 Python 3 interpreter (default: python3)
#   GNN_RUNTIME_PYTHON     interpreter with the pinned GNN distribution installed
#   GNN_ROOT               Generalized_Notation_Notation checkout to install the
#                          pinned commit from, instead of the pinned repository
#   ACTINF_GATE_DIR        where `gnn` provisions a runtime (default: .gate)
#
# `gnn` runs in one environment: GNN_RUNTIME_PYTHON when set, and otherwise the
# commit recorded in specs/gnn-pin.json installed into $ACTINF_GATE_DIR with uv
# (from GNN_ROOT when that is set). CI uses the provisioned path. The arm then
# runs the shared `python -m gnn.importers check` reader and the model
# conformance check against that one installed revision.
#
# There is no `types` arm: this is a Julia repository with no static type
# checker, and test/runtests.jl is the checked contract.
# usage:end

set -euo pipefail

ROOT=$(cd -- "$(dirname -- "${BASH_SOURCE[0]}")" && pwd)
cd "$ROOT"

JULIA=${JULIA_BIN:-julia}
PYTHON=${PYTHON:-python3}
GATE_DIR=${ACTINF_GATE_DIR:-.gate}

usage() {
    sed -n '/^# usage:begin$/,/^# usage:end$/p' "${BASH_SOURCE[0]}" |
        sed '1d;$d' | sed 's/^# \{0,1\}//'
}

# Every arm sequences its subcommands with `&&` or an explicit `return`, never
# by relying on `set -e`: the dispatcher calls an arm inside a tested context
# (`run_arm "$arm" || status=$?`), and Bash suppresses errexit for a whole
# function in that context. Without the explicit chains a failed link check or
# failed `lint` would be swallowed whenever the next command succeeded.
arm_lint() {
    "$PYTHON" scripts/lint.py
}

arm_fast() {
    ACTINF_RXINFER_TEST_ARM=fast "$JULIA" --project=. --startup-file=no test/runtests.jl
}

arm_full() {
    "$JULIA" --project=. --startup-file=no -e 'using Pkg; Pkg.test()'
}

arm_docs() {
    "$PYTHON" scripts/check_links.py &&
        "$PYTHON" scripts/gate_report.py --check
}

provision_gnn_runtime() {
    local pin=specs/gnn-pin.json venv="$GATE_DIR/gnn-runtime" marker repo commit source
    if ! command -v uv >/dev/null 2>&1; then
        echo "run.sh gnn: uv is required to provision the pinned GNN runtime;" \
             "set GNN_RUNTIME_PYTHON to use an existing install" >&2
        return 2
    fi
    repo=$("$PYTHON" -c 'import json,sys; print(json.load(open(sys.argv[1]))["repository"])' "$pin")
    commit=$("$PYTHON" -c 'import json,sys; print(json.load(open(sys.argv[1]))["commit"])' "$pin")
    source=$repo
    if [ -n "${GNN_ROOT:-}" ]; then
        source="file://$(cd "$GNN_ROOT" && pwd)"
    fi
    marker="$venv/.pin-commit"
    if [ -x "$venv/bin/python" ] && [ -f "$marker" ] && [ "$(cat "$marker")" = "$commit" ]; then
        return 0
    fi
    echo "run.sh gnn: provisioning gnn from $commit into $venv" >&2
    mkdir -p "$GATE_DIR"
    if [ ! -x "$venv/bin/python" ]; then
        uv venv --python 3.12 "$venv" >&2 || return $?
    fi
    uv pip install --python "$venv/bin/python" \
        "generalized-notation-notation @ git+${source}@${commit}" >&2
    printf '%s\n' "$commit" > "$marker"
}

# The pin, the `.github/GNN.md` pointer and the declared specification are the
# shared reader's subject: `gnn.importers` in the pinned environment decides
# them, so this repository keeps no second copy of that logic.
arm_gnn() {
    local runtime=${GNN_RUNTIME_PYTHON:-}
    if [ -z "$runtime" ]; then
        provision_gnn_runtime || return $?
        runtime="$GATE_DIR/gnn-runtime/bin/python"
    fi
    "$runtime" -m gnn.importers check --repo . --require-pointer \
        --workflow .github/workflows/ci.yml --job gnn-conformance || return $?
    "$PYTHON" scripts/validate_gnn_spec.py --gnn-runtime "$runtime" --julia "$JULIA" --json
}

if [ "$#" -eq 0 ]; then
    set -- lint fast
fi

case "$1" in
    measure)
        shift
        exec "$PYTHON" scripts/gate_report.py "$@"
        ;;
    -h | --help | help)
        usage
        exit 0
        ;;
esac

status=0
for arm in "$@"; do
    echo "==> run.sh $arm"
    case "$arm" in
        lint) arm_lint ;;
        fast) arm_fast ;;
        full) arm_full ;;
        docs) arm_docs ;;
        gnn) arm_gnn ;;
        all) arm_lint && arm_full && arm_docs && arm_gnn ;;
        *)
            echo "run.sh: unknown arm '$arm'; run ./run.sh --help" >&2
            status=2
            ;;
    esac || status=$?
    [ "$status" -eq 0 ] || break
done
exit "$status"
