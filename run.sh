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
#   GNN_TAG_STORE          Git store with the pinned tag fetched for offline use
#   GNN_BOOTSTRAP          independently reviewed, SHA-256-bound bootstrap file
#   GNN_SOURCE_MANIFEST    frozen complete v5.1.0 package manifest
#   GNN_ORIGIN_MODE        installed (default), or explicit source admission
#   GNN_PACKAGE_ROOT       selected gnn directory; required in source mode
#   ACTINF_GATE_DIR        where `gnn` provisions a runtime (default: .gate)
#
# `gnn` uses GNN_RUNTIME_PYTHON when set; installed mode otherwise provisions the
# pin from its canonical repository into $ACTINF_GATE_DIR with uv. Source mode requires
# an explicit runtime and artifact. Both modes require the independent bootstrap
# and full manifest above before any GNN import. The arm checks model conformance
# (resolving the live tag, or GNN_TAG_STORE offline), then the producer's shared
# pin/pointer/document checker, then regression tests. Each verdict has its own
# guarded lifetime, including exit revalidation; -m gnn.importers is not safe.
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
    ACTINF_RXINFER_TEST_ARM=full "$JULIA" --project=. --startup-file=no -e 'using Pkg; Pkg.test()'
}

arm_docs() {
    "$PYTHON" scripts/check_links.py &&
        "$PYTHON" scripts/gate_report.py --check
}

provision_gnn_runtime() {
    local pin=specs/gnn-pin.json venv="$GATE_DIR/gnn-runtime" marker repo commit source
    local cached_commit pending_marker status pin_record
    if [ -n "${GNN_ROOT:-}" ]; then
        echo "run.sh gnn: GNN_ROOT local-checkout provisioning cannot satisfy canonical Git provenance;" \
             "use canonical provisioning or explicit GNN_ORIGIN_MODE=source with GNN_PACKAGE_ROOT" >&2
        return 2
    fi
    if ! command -v uv >/dev/null 2>&1; then
        echo "run.sh gnn: uv is required to provision the pinned GNN runtime;" \
             "set GNN_RUNTIME_PYTHON to use an existing install" >&2
        return 2
    fi
    # Normalize/admit the exact current pin with the independently checked
    # producer before choosing any installation source. The JSON below is that
    # producer's data result, not a second reader of the unchecked pin file.
    pin_record=$("$PYTHON" scripts/gnn_source.py pin --pin "$pin") || return $?
    repo=$("$PYTHON" -c 'import json,sys; print(json.loads(sys.argv[1])["repository"])' "$pin_record") || return $?
    commit=$("$PYTHON" -c 'import json,sys; print(json.loads(sys.argv[1])["commit"])' "$pin_record") || return $?
    source="https://github.com/$repo"
    marker="$venv/.pin-commit"
    if [ -x "$venv/bin/python" ] && [ -f "$marker" ]; then
        cached_commit=$(cat "$marker") || return $?
        if [ "$cached_commit" = "$commit" ]; then
            return 0
        fi
    fi
    echo "run.sh gnn: provisioning gnn from $commit into $venv" >&2
    # An in-place update can change the runtime even when uv later fails.
    # Retire its old readiness before the first mutation, not after installation.
    rm -f -- "$marker" || return $?
    mkdir -p -- "$GATE_DIR" || return $?
    if [ ! -x "$venv/bin/python" ]; then
        uv venv --python 3.12 "$venv" >&2 || return $?
    fi
    uv pip install --python "$venv/bin/python" \
        "generalized-notation-notation @ git+${source}@${commit}" >&2 || return $?
    # A failed marker write must not leave a readable success marker either.
    pending_marker=$(mktemp "$venv/.pin-commit.XXXXXX") || return $?
    if printf '%s\n' "$commit" > "$pending_marker" &&
        mv -f -- "$pending_marker" "$marker"; then
        return 0
    else
        status=$?
        rm -f -- "$pending_marker"
        return "$status"
    fi
}

# The reviewed producer owns pin normalization, complete source/origin admission
# and the shared checker. The adapter only binds the independent resource hashes;
# it does not import the target package to discover its own expected identity.
arm_gnn() {
    local runtime=${GNN_RUNTIME_PYTHON:-}
    if [ -z "$runtime" ]; then
        if [ "${GNN_ORIGIN_MODE:-installed}" = source ]; then
            echo "run.sh gnn: source mode requires GNN_RUNTIME_PYTHON" >&2
            return 2
        fi
        provision_gnn_runtime || return $?
        runtime="$GATE_DIR/gnn-runtime/bin/python"
    fi
    local tag_check=(--verify-tag-remote)
    if [ -n "${GNN_TAG_STORE:-}" ]; then
        tag_check=(--verify-tag-store "$GNN_TAG_STORE")
    fi
    "$PYTHON" scripts/validate_gnn_spec.py --gnn-runtime "$runtime" --julia "$JULIA" \
        "${tag_check[@]}" --json || return $?
    # The same selected runtime runs the checked standalone producer, never an
    # unchecked `-m gnn.importers` import. It revalidates on scope exit too.
    "$runtime" -P scripts/gnn_source.py check --repo . --require-pointer \
        --workflow .github/workflows/ci.yml --job gnn-conformance || return $?
    # Children retain the selected runtime; host Python never imports GNN.
    GNN_RUNTIME_PYTHON="$runtime" "$PYTHON" -m unittest discover -s test -p 'test_*.py'
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
