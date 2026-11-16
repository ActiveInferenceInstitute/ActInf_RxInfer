"""Validate the committed GNN model with an independently admitted parser.

The producer-owned standalone bootstrap reads the existing pin without importing
gnn. Its checked bytes and independently frozen complete v5.1.0 source manifest
are selected with --gnn-bootstrap/GNN_BOOTSTRAP and
--gnn-source-manifest/GNN_SOURCE_MANIFEST. Every parser/verdict import and call
runs in a fresh selected-runtime subprocess inside qualified_source, including
exit revalidation. Installed mode requires matching PEP 610 Git origin and full
content; explicit source mode requires --gnn-package-root/GNN_PACKAGE_ROOT and
does not certify an installed distribution. Neither mode changes the pin.

The tag check remains optional here and mandatory in run.sh gnn: remote mode
resolves the live tag; --verify-tag-store uses an independently prepared store.
No requested-but-unavailable tag or Julia reader can become a pass.

The document remains the model's single source of truth. Conformance compares
its name, variables, dimensions, graph, scalars, posterior equations and ontology
with the pinned parser, semantic validator and consistency checker. Scalars
also agree with the regex reader and, when requested, the dependency-free Julia
reader. All comparisons outside the child consume JSON data, not GNN objects.

Exit codes: 0 pass, 1 conformance failure, 2 not run (runtime, admission, requested
tag resolution or requested Julia reader unavailable). This is the first step
of run.sh gnn; the shared producer checker is independently guarded afterward.
"""

from __future__ import annotations

import argparse
import importlib.util
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

#: Named failures: the pin's tag and commit are one revision, and the pin's
#: language version is the document's and the parser's.
TAG_COMMIT_MISMATCH = "tag-commit-mismatch"
LANGUAGE_VERSION_MISMATCH = "language-version-mismatch"

#: ``-P`` keeps the working directory (``-c``) and the script directory off
#: ``sys.path``, so every process that imports the pinned package resolves it
#: from ``PYTHONPATH`` and site-packages. The pinned distribution declares
#: ``requires-python >=3.11``, the version that added the flag.
SAFE_PATH = "-P"

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


_source_spec = importlib.util.spec_from_file_location(
    "actinf_rxinfer_gnn_source", ROOT / "scripts" / "gnn_source.py"
)
source = importlib.util.module_from_spec(_source_spec)
sys.modules[_source_spec.name] = source
_source_spec.loader.exec_module(source)
Unavailable = source.Unavailable




def read_pin(python: str, path: Path, *, source_args: list[str]) -> dict[str, Any]:
    """Ask the checked producer bootstrap for pin data in the selected runtime."""
    output = _run_text(
        [
            python, SAFE_PATH, str(ROOT / "scripts" / "gnn_source.py"), "pin",
            "--pin", str(path.absolute()), *source_args,
        ],
        what=f"reviewed GNN pin reader could not run with {python}",
    )
    try:
        return json.loads(output)
    except json.JSONDecodeError as exc:
        raise Unavailable(f"reviewed GNN pin reader printed no pin for {path}: {exc}") from exc




def _run_text(command: list[str], *, what: str) -> str:
    try:
        completed = subprocess.run(
            command, stdin=subprocess.DEVNULL, capture_output=True, text=True, check=False
        )
    except OSError as exc:
        raise Unavailable(f"{what}: {exc}") from exc
    if completed.returncode != 0:
        detail = (completed.stderr or completed.stdout).strip().splitlines()
        tail = " | ".join(detail[-3:]) if detail else "no output"
        raise Unavailable(f"{what}: {tail}")
    return completed.stdout




def remote_url(repository: str) -> str:
    """Return a git URL for the pin's repository.

    ``gnn.importers`` normalizes the pin's repository to ``owner/name`` for a
    GitHub URL; ``git ls-remote`` needs the full URL.
    """

    if "://" in repository or repository.startswith("git@") or repository.startswith("/"):
        return repository
    return f"https://github.com/{repository}"


def tag_binding(
    pin: dict[str, Any], *, remote: bool = False, store: Path | None = None
) -> dict[str, Any]:
    """Resolve the exact tag from upstream or an explicitly prepared Git store.

    The store records an earlier fetch. Only remote mode checks the live tag.
    """

    tag = pin["tag"]
    record: dict[str, Any] = {
        "status": "unresolvable-offline",
        "tag": tag,
        "commit": pin["commit"],
        "resolved": None,
        "detail": "remote tag resolution was not requested (--verify-tag-remote)",
    }
    if store is not None:
        git = ["git", "--no-replace-objects", "-C", str(store)]
        env = dict(os.environ, GIT_NO_LAZY_FETCH="1")
        try:
            origin = subprocess.run(
                [*git, "config", "--local", "--get-all", "remote.origin.url"],
                stdin=subprocess.DEVNULL, capture_output=True, text=True, check=True, env=env,
                timeout=10,
            ).stdout.splitlines()
            expected = remote_url(pin["repository"]).rstrip("/").removesuffix(".git")
            if len(origin) != 1 or origin[0].rstrip("/").removesuffix(".git") != expected:
                record["detail"] = "the local tag store origin differs from the pinned repository"
                return record
            resolved = subprocess.run(
                [*git, "rev-parse", "--verify", f"refs/tags/{tag}^{{commit}}"],
                stdin=subprocess.DEVNULL, capture_output=True, text=True, check=True, env=env,
                timeout=10,
            ).stdout.strip()
        except (OSError, subprocess.SubprocessError) as exc:
            record["detail"] = f"the local tag store could not resolve {tag}: {exc}"
            return record
        record.update(status="verified", resolved=resolved, detail="prepared local Git tag store")
        return record
    if not remote:
        return record
    try:
        completed = subprocess.run(
            ["git", "ls-remote", "--tags", remote_url(pin["repository"]), f"refs/tags/{tag}*"],
            capture_output=True,
            stdin=subprocess.DEVNULL,
            text=True,
            check=False,
        )
    except OSError as exc:
        record["detail"] = f"git ls-remote could not run: {exc}"
        return record
    if completed.returncode != 0:
        record["detail"] = f"git ls-remote failed: {completed.stderr.strip()}"
        return record
    pairs = [line.split() for line in completed.stdout.splitlines() if len(line.split()) == 2]
    # An annotated tag lists the tag object and, peeled, the commit it names; the
    # peeled entry is the commit.
    for wanted in (f"refs/tags/{tag}^{{}}", f"refs/tags/{tag}"):
        for sha, name in pairs:
            if name == wanted:
                record.update(status="verified", resolved=sha, detail="git ls-remote")
                return record
    record["detail"] = f"tag {tag} is not listed by {pin['repository']}"
    return record


def tag_failures(tag: dict[str, Any] | None, pin: dict[str, Any]) -> list[str]:
    """Return the named failure when the pin's tag resolves to a different commit."""

    if tag is not None and tag.get("status") == "verified" and tag.get("resolved") != pin["commit"]:
        return [
            f"{TAG_COMMIT_MISMATCH}: tag {pin['tag']} resolves to {tag.get('resolved')} "
            f"but the pin records {pin['commit']}"
        ]
    return []


_LANGUAGE_VERSION = re.compile(r"(?i)^\s*(?:GNN\s*)?v?(\d+(?:\.\d+)*)")


def normalize_language_version(text: object) -> str | None:
    """Return ``1.1`` for ``GNN v1.1``, ``v1.1`` or ``1.1``; ``None`` when unparseable."""

    match = _LANGUAGE_VERSION.match(str(text))
    return match.group(1) if match else None


def document_language_version(spec_text: str) -> str | None:
    """Return the normalized version in the document's GNNVersionAndFlags section."""

    match = re.search(r"(?ms)^##[ \t]+GNNVersionAndFlags[ \t]*$(.*?)(?=^##[ \t]|\Z)", spec_text)
    if match is None:
        return None
    for line in match.group(1).splitlines():
        if line.strip() and not line.lstrip().startswith(("#", "<!--")):
            return normalize_language_version(line)
    return None


def language_version_failures(
    pin: dict[str, Any], *, document: str | None, parser: object
) -> list[str]:
    """Return failures when pin, document and parser disagree on the language version."""

    expected = normalize_language_version(pin.get("language_version"))
    if expected is None:
        return [f"{LANGUAGE_VERSION_MISMATCH}: the pin's language_version is not parseable"]
    failures = []
    if document != expected:
        failures.append(
            f"{LANGUAGE_VERSION_MISMATCH}: the document declares {document!r}, "
            f"the pin records {expected!r}"
        )
    if normalize_language_version(parser) != expected:
        failures.append(
            f"{LANGUAGE_VERSION_MISMATCH}: the pinned parser reports {parser!r}, "
            f"the pin records {expected!r}"
        )
    return failures


def run_probe(
    python: str, spec: Path, output: Path, *, pin: Path, source_args: list[str]
) -> dict[str, Any]:
    """Run the self-guarding probe; return only its exit-revalidated JSON."""
    _run_text(
        [
            python, SAFE_PATH, str(PROBE), "--spec", str(spec.absolute()),
            "--pin", str(pin.absolute()), "--output", str(output), *source_args,
        ],
        what=f"pinned parser probe failed with {python}",
    )
    try:
        payload = json.loads(output.read_text(encoding="utf-8"))
    except (OSError, ValueError) as exc:
        raise Unavailable(f"pinned parser probe produced no receipt: {exc}") from exc
    qualification = payload.get("source_qualification", {})
    if not (
        qualification.get("ok") is True
        and qualification.get("imports_verified") is True
        and qualification.get("preimport") is True
        and qualification.get("status") == "qualified"
        and qualification.get("commit") == source.COMMIT
        and qualification.get("manifest_sha256") == source.MANIFEST_SHA256
    ):
        raise Unavailable("pinned parser probe did not complete source qualification")
    return payload


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
    package_dir: Path | None = None,
    tag: dict[str, Any] | None = None,
) -> list[str]:
    """Return every conformance failure between the document and the model."""

    failures: list[str] = []
    parser = payload["parser"]
    expected_version = pin["tag"].lstrip("v")

    if payload["gnn_version"] != expected_version:
        failures.append(
            f"parser version {payload['gnn_version']} differs from the pinned {expected_version}"
        )
    failures.extend(tag_failures(tag, pin))
    if package_dir is not None:
        module = Path(str(payload["gnn_module"])).resolve()
        if not module.is_relative_to(package_dir):
            failures.append(
                f"parser was imported from {module}, outside the verified package {package_dir}"
            )
    failures.extend(
        language_version_failures(
            pin, document=document_language_version(spec_text), parser=parser["version"]
        )
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
    tag_mode = parser.add_mutually_exclusive_group()
    tag_mode.add_argument(
        "--verify-tag-remote",
        action="store_true",
        help="resolve the pin's tag upstream with git ls-remote (needs network access)",
    )
    tag_mode.add_argument(
        "--verify-tag-store",
        type=Path,
        help="resolve the pin's tag from an explicitly prepared Git store (offline)",
    )
    parser.add_argument("--spec", type=Path, default=GNN_SPEC_PATH)
    parser.add_argument("--pin", type=Path, default=GNN_PIN_PATH)
    parser.add_argument("--receipt", type=Path, default=DEFAULT_RECEIPT)
    parser.add_argument("--json", action="store_true", help="print the receipt to stdout")
    source.add_arguments(parser)
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
            source_args = source.command_arguments(args)
            pin = read_pin(args.gnn_runtime, args.pin, source_args=source_args)
            tag = tag_binding(pin, remote=args.verify_tag_remote, store=args.verify_tag_store)
            if (args.verify_tag_remote or args.verify_tag_store) and tag["status"] != "verified":
                flag = "--verify-tag-remote" if args.verify_tag_remote else "--verify-tag-store"
                raise Unavailable(f"{flag}: {tag['detail']}")
            payload = run_probe(
                args.gnn_runtime, args.spec, output, pin=args.pin, source_args=source_args
            )
            qualification = payload["source_qualification"]
            package_dir = Path(qualification["package_root"])
            admitted_origin = qualification["origin"]
            revision = {
                "status": "verified" if admitted_origin["vcs_verified"] else "explicit-source",
                "commit": qualification["commit"],
                "detail": admitted_origin,
            }
            origin = f"{admitted_origin['kind']} runtime {args.gnn_runtime} ({package_dir})"
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
            package_dir=package_dir,
            tag=tag,
        )

    receipt = {
        "ok": not failures,
        "spec": str(args.spec),
        "pin": pin,
        "pin_source": origin,
        "gnn_version": payload["gnn_version"],
        "gnn_module": payload["gnn_module"],
        "language_version": pin["language_version"],
        "parser_language_version": payload["parser"].get("version"),
        "tag_binding": tag,
        "revision": revision,
        "source_qualification": qualification,
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
        f"({origin}); language version {payload['parser'].get('version')}; "
        f"tag {tag['tag']} -> {tag['status']}; revision {revision['status']}; "
        f"{reader}; receipt {args.receipt}"
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
