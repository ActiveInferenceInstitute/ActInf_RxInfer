"""Validate the committed GNN specification with the pinned upstream parser.

The canonical GNN pin is recorded in ``specs/gnn-pin.json`` (repository, tag,
commit, and SHA-256 digests of the parser files). The pin is read — and the
pointer and the specification are checked — by the shared reader
``gnn.importers`` run from the pinned environment; this script does not parse
the pin's shape a second time. It uses one verified source: a pinned installed
runtime (``--gnn-runtime`` or ``GNN_RUNTIME_PYTHON``), an interpreter whose
``gnn`` package is installed at the pinned revision. The distribution version
and the installed parser file digests are verified before the document is
parsed, so the live working tree is never imported.

The document is parsed by ``scripts/gnn_parser_probe.py`` in a subprocess and
checked for conformance. ``specs/coin_flip.gnn.md`` is the single source of
truth for the model, so the checks cover the declared model name, the declared
variables and their dimensions, the connection graph, the declared scalars, the
conjugate-posterior equations, and the ontology annotations, plus the pinned
semantic validator and consistency checker.

The declared scalars are compared against three independent readers of the same
document: the pinned parser, the regular-expression reader in this script, and
the dependency-free Julia reader in ``src/spec_reader.jl``
(``--julia`` or ``JULIA_BIN``, used by the Julia test suite as well).

Exit codes: ``0`` pass, ``1`` conformance failure, ``2`` pinned runtime or
requested Julia reader unavailable (the run is then explicitly *not run*, never
a pass).

Usage:

    python3 scripts/validate_gnn_spec.py --gnn-runtime /path/to/venv/bin/python \\
        --julia julia --json

This is the second step of ``./run.sh gnn``, after
``python -m gnn.importers check --repo . --require-pointer`` in the same
interpreter.
"""

from __future__ import annotations

import argparse
import hashlib
import json
import os
import re
import shutil
import subprocess
import sys
import tempfile
from pathlib import Path
from typing import Any

ROOT = Path(__file__).resolve().parents[1]
PROBE = ROOT / "scripts" / "gnn_parser_probe.py"
GNN_SPEC_PATH = ROOT / "specs" / "coin_flip.gnn.md"
GNN_PIN_PATH = ROOT / "specs" / "gnn-pin.json"
DEFAULT_RECEIPT = ROOT / "docs" / "_build" / "gnn" / "validation-receipt.json"
PACKAGE_PREFIX = "src/gnn/"

# Expectations of the pinned document. These are the declarations the Julia
# implementation and the released example rely on; changing the model means
# changing the document, this block, and the recorded output together.
MODEL_NAME = "ActInf_RxInfer Beta-Bernoulli Coin Flip"
VARIABLES = {"theta": [1], "y": [500, 1], "k": [1], "a": [1], "b": [1]}
CONNECTIONS = [
    (["a"], ["theta"]),
    (["b"], ["theta"]),
    (["theta"], ["y"]),
    (["y"], ["k"]),
]
SCALARS = {"a": 2.0, "b": 2.0, "theta_true": 0.75, "n_observations": 500, "seed": 123}
ONTOLOGY = {
    "theta": "HiddenState",
    "y": "Observation",
    "k": "SufficientStatistic",
    "a": "PriorConcentrationA",
    "b": "PriorConcentrationB",
}
EQUATIONS = (
    "theta ~ Beta(a, b)",
    "y_i | theta ~ Bernoulli(theta)",
    "k = sum",
    "theta | y ~ Beta(a + k, b + n - k)",
)
REQUIRED_SECTIONS = (
    "GNNSection",
    "GNNVersionAndFlags",
    "ModelName",
    "ModelAnnotation",
    "StateSpaceBlock",
    "Connections",
    "InitialParameterization",
    "Equations",
    "Time",
    "ActInfOntologyAnnotation",
    "ModelParameters",
    "Footer",
    "Signature",
)
SCALAR_PATTERN = re.compile(r"(?m)^[ \t]*([A-Za-z_]\w*)[ \t]*=[ \t]*\{[ \t]*\(([^)]*)\)[ \t]*\}")
READER_EXPRESSION = (
    'include(joinpath(pwd(), "src", "spec_reader.jl")); print(spec_summary(ARGS[1]))'
)


class Unavailable(RuntimeError):
    """Raised when the pinned parser runtime or checkout is not available."""


def _sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for block in iter(lambda: handle.read(1 << 20), b""):
            digest.update(block)
    return digest.hexdigest()


PIN_READER_PROGRAM = """\
import json, sys
from pathlib import Path

from gnn.importers import read_pin

pin = read_pin(Path(sys.argv[1]))
print(json.dumps({
    "path": str(pin.path),
    "schema": pin.schema,
    "repository": pin.repository,
    "tag": pin.tag,
    "commit": pin.commit,
    "recorded": pin.recorded,
    "spec_files": list(pin.spec_files),
    "parser_files": pin.raw.get("parser_files") or {},
}))
"""


def read_pin(python: str, path: Path) -> dict[str, Any]:
    """Read the pin with the shared reader installed in ``python``.

    ``gnn.importers.read_pin`` is the estate's one normalizer for the pin
    shapes; this script asks it for the facts it needs instead of deciding
    which keys carry the revision, the tag or the digests.
    """

    try:
        completed = subprocess.run(
            [python, "-c", PIN_READER_PROGRAM, str(path)],
            capture_output=True,
            text=True,
            check=False,
        )
    except OSError as exc:
        raise Unavailable(f"gnn.importers could not run with {python}: {exc}") from exc
    if completed.returncode != 0:
        detail = (completed.stderr or completed.stdout).strip().splitlines()
        tail = " | ".join(detail[-3:]) if detail else "no output"
        raise Unavailable(f"gnn.importers could not read {path}: {tail}")
    try:
        pin = json.loads(completed.stdout)
    except json.JSONDecodeError as exc:
        raise Unavailable(f"gnn.importers printed no pin for {path}: {exc}") from exc
    if not pin.get("tag"):
        raise Unavailable(f"pin record {path} records no release tag")
    digests = pin.get("parser_files")
    if not isinstance(digests, dict) or not digests:
        raise Unavailable(f"pin record {path} records no parser_files digests")
    return pin


def _verify_digests(package_dir: Path, pin: dict[str, Any], *, origin: str) -> dict[str, str]:
    """Verify every recorded parser digest under an installed ``gnn`` package."""

    observed: dict[str, str] = {}
    for relative, expected in sorted(pin["parser_files"].items()):
        suffix = relative[len(PACKAGE_PREFIX) :] if relative.startswith(PACKAGE_PREFIX) else relative
        path = package_dir / suffix
        if not path.is_file():
            raise Unavailable(f"pinned parser file is missing from {origin}: {suffix}")
        observed[relative] = _sha256(path)
        if observed[relative] != expected:
            raise Unavailable(
                f"pinned parser file digest mismatch for {suffix} in {origin}: "
                f"expected {expected}, observed {observed[relative]}"
            )
    return observed


def run_probe(python: str, spec: Path, output: Path) -> dict[str, Any]:
    """Run the pinned parser probe in a subprocess and return its payload."""

    try:
        completed = subprocess.run(
            [python, str(PROBE), "--spec", str(spec), "--output", str(output)],
            capture_output=True,
            text=True,
            check=False,
        )
    except OSError as exc:
        raise Unavailable(f"pinned parser probe could not run with {python}: {exc}") from exc
    if completed.returncode != 0:
        detail = (completed.stderr or completed.stdout).strip().splitlines()
        tail = " | ".join(detail[-3:]) if detail else "no output"
        raise Unavailable(
            f"pinned parser probe failed with {python}: {tail}. Provide an interpreter that "
            "has the GNN parser dependencies (a runtime installed from the pinned revision) "
            "via --gnn-runtime."
        )
    return json.loads(output.read_text(encoding="utf-8"))


def run_julia_reader(julia: str, spec: Path) -> dict[str, str]:
    """Run the dependency-free Julia reader on ``spec`` and return its summary."""

    if shutil.which(julia) is None and not Path(julia).is_file():
        raise Unavailable(f"julia reader interpreter not found: {julia}")
    completed = subprocess.run(
        [julia, "--startup-file=no", "--history-file=no", "-e", READER_EXPRESSION, str(spec)],
        cwd=ROOT,
        capture_output=True,
        text=True,
        check=False,
    )
    if completed.returncode != 0:
        detail = (completed.stderr or completed.stdout).strip().splitlines()
        tail = " | ".join(detail[-3:]) if detail else "no output"
        raise Unavailable(f"julia reader failed with {julia}: {tail}")
    summary = {}
    for line in completed.stdout.splitlines():
        if "=" in line:
            key, value = line.split("=", 1)
            summary[key.strip()] = value.strip()
    if not summary:
        raise Unavailable("the julia reader produced no summary lines")
    return summary


def declared_scalars(spec_text: str) -> dict[str, float]:
    """Read ``name={(value)}`` declarations from the InitialParameterization section."""

    match = re.search(r"(?ms)^##[ \t]+InitialParameterization[ \t]*$(.*?)(?=^##[ \t]|\Z)", spec_text)
    if match is None:
        return {}
    return {
        name: float(value.strip())
        for name, value in SCALAR_PATTERN.findall(match.group(1))
    }


def parsed_scalars(parser: dict[str, Any]) -> dict[str, float]:
    """Flatten the pinned parser's own view of the declared scalars."""

    observed: dict[str, float] = {}
    for name, value in parser["parameters"].items():
        while isinstance(value, list) and len(value) == 1:
            value = value[0]
        if isinstance(value, (int, float)) and not isinstance(value, bool):
            observed[name] = float(value)
    return observed


def _variable_dimensions(parser: dict[str, Any]) -> dict[str, list[int]]:
    return {variable["name"]: list(variable["dimensions"]) for variable in parser["variables"]}


def conformance_failures(
    payload: dict[str, Any],
    *,
    pin: dict[str, Any],
    spec_text: str,
    julia_summary: dict[str, str] | None,
) -> list[str]:
    """Return every conformance failure between the document and the model."""

    failures: list[str] = []
    parser = payload["parser"]
    expected_version = pin["tag"].lstrip("v")

    if payload["gnn_version"] != expected_version:
        failures.append(
            f"parser version {payload['gnn_version']} differs from the pinned {expected_version}"
        )
    if not parser["success"]:
        failures.append("pinned parser reported failure")
    for message in parser["errors"]:
        failures.append(f"parser error: {message}")
    for message in parser["warnings"]:
        failures.append(f"parser warning: {message}")

    if parser["model_name"] != MODEL_NAME:
        failures.append(
            f"declared model name {parser['model_name']!r} differs from {MODEL_NAME!r}"
        )

    dimensions = _variable_dimensions(parser)
    if dimensions != VARIABLES:
        failures.append(f"declared variables {dimensions} differ from {VARIABLES}")
    if dimensions.get("y") != [SCALARS["n_observations"], 1]:
        failures.append(
            f"StateSpaceBlock y dimensions {dimensions.get('y')} do not match the declared "
            f"n_observations {SCALARS['n_observations']}"
        )

    connections = [
        (list(connection["sources"]), list(connection["targets"]))
        for connection in parser["connections"]
    ]
    if connections != CONNECTIONS:
        failures.append(f"declared connections {connections} differ from {CONNECTIONS}")

    for name, expected in SCALARS.items():
        for label, observed in (
            ("regex", declared_scalars(spec_text)),
            ("parser", parsed_scalars(parser)),
        ):
            if observed.get(name) != expected:
                failures.append(
                    f"{label} reader sees {name}={observed.get(name)} instead of {expected}"
                )
    if julia_summary is not None:
        if julia_summary.get("model_name") != MODEL_NAME:
            failures.append(
                f"julia reader sees model_name={julia_summary.get('model_name')!r} "
                f"instead of {MODEL_NAME!r}"
            )
        julia_scalars = {
            "prior_a": SCALARS["a"],
            "prior_b": SCALARS["b"],
            "theta_true": SCALARS["theta_true"],
            "n_observations": SCALARS["n_observations"],
            "seed": SCALARS["seed"],
        }
        for name, expected in julia_scalars.items():
            observed = julia_summary.get(name)
            if observed is None or float(observed) != float(expected):
                failures.append(
                    f"julia reader sees {name}={observed} instead of {expected} "
                    "(src/spec_reader.jl must read the committed declarations)"
                )

    for fragment in EQUATIONS:
        if fragment not in spec_text:
            failures.append(f"equations do not state the model fragment {fragment!r}")

    ontology = {mapping["variable"]: mapping["term"] for mapping in parser["ontology_mappings"]}
    if ontology != ONTOLOGY:
        failures.append(f"ontology annotations {ontology} differ from {ONTOLOGY}")

    sections = set(parser["sections"])
    missing = [section for section in REQUIRED_SECTIONS if section not in sections]
    if missing:
        failures.append(f"document is missing the sections {missing}")
    if "Static" not in str(parser["time_specification"]):
        failures.append(f"declared time specification {parser['time_specification']!r} is not Static")

    semantic = payload["semantic"]
    if not semantic.get("is_valid"):
        failures.append(
            f"pinned semantic validator rejected the document: {semantic.get('errors')}"
        )
    for message in semantic.get("warnings", []):
        failures.append(f"semantic warning: {message}")

    consistency = payload["consistency"]
    if not consistency.get("consistent"):
        failures.append(f"pinned consistency checker reported: {consistency.get('warnings')}")

    return failures


def main(argv: list[str] | None = None) -> int:
    """Validate the committed specification against the pinned parser."""

    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--gnn-runtime",
        default=os.environ.get("GNN_RUNTIME_PYTHON"),
        help="interpreter with the pinned GNN distribution installed",
    )
    parser.add_argument(
        "--julia",
        default=os.environ.get("JULIA_BIN"),
        help="julia interpreter for the dependency-free spec reader (default: $JULIA_BIN)",
    )
    parser.add_argument("--spec", type=Path, default=GNN_SPEC_PATH)
    parser.add_argument("--pin", type=Path, default=GNN_PIN_PATH)
    parser.add_argument("--receipt", type=Path, default=DEFAULT_RECEIPT)
    parser.add_argument("--json", action="store_true", help="print the receipt to stdout")
    args = parser.parse_args(argv)

    if not args.gnn_runtime:
        print(
            "gnn validation not run: supply --gnn-runtime/GNN_RUNTIME_PYTHON",
            file=sys.stderr,
        )
        return 2

    with tempfile.TemporaryDirectory(prefix="actinf-rxinfer-gnn-") as directory:
        output = Path(directory) / "probe.json"
        try:
            pin = read_pin(args.gnn_runtime, args.pin)
            payload = run_probe(args.gnn_runtime, args.spec, output)
            package_dir = Path(str(payload["gnn_module"])).resolve().parent
            _verify_digests(package_dir, pin, origin=args.gnn_runtime)
            origin = f"installed runtime {args.gnn_runtime} ({package_dir})"
        except Unavailable as exc:
            print(f"gnn validation not run: {exc}", file=sys.stderr)
            return 2

        julia_summary = None
        if args.julia:
            try:
                julia_summary = run_julia_reader(args.julia, args.spec)
            except Unavailable as exc:
                print(f"gnn validation not run: {exc}", file=sys.stderr)
                return 2

        failures = conformance_failures(
            payload,
            pin=pin,
            spec_text=args.spec.read_text(encoding="utf-8"),
            julia_summary=julia_summary,
        )

    receipt = {
        "ok": not failures,
        "spec": str(args.spec),
        "pin": pin,
        "pin_source": origin,
        "gnn_version": payload["gnn_version"],
        "gnn_module": payload["gnn_module"],
        "parser_success": payload["parser"]["success"],
        "semantic_valid": payload["semantic"].get("is_valid"),
        "consistency_score": payload["consistency"].get("consistency_score"),
        "julia_reader": julia_summary,
        "failures": failures,
    }
    args.receipt.parent.mkdir(parents=True, exist_ok=True)
    args.receipt.write_text(json.dumps(receipt, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    if args.json:
        print(json.dumps(receipt, sort_keys=True))
    if failures:
        print("gnn conformance failures:", file=sys.stderr)
        for message in failures:
            print(f"  {message}", file=sys.stderr)
        return 1
    reader = (
        f"and the julia reader ({julia_summary['model_name']})"
        if julia_summary is not None
        else "and no julia reader was requested"
    )
    print(
        f"gnn validation passed: {args.spec} parsed by gnn {payload['gnn_version']} "
        f"({origin}); {reader}; receipt {args.receipt}"
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
