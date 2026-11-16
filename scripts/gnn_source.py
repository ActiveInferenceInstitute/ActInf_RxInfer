"""Run the independently reviewed GNN bootstrap, never an unchecked GNN import.

GNN_BOOTSTRAP and GNN_SOURCE_MANIFEST select the producer-owned resources whose
identities are frozen below. They are inputs, not generated from the runtime.
Installed mode requires the producer's complete-content and PEP 610 admission.
Explicit source mode additionally requires GNN_PACKAGE_ROOT (the gnn directory),
selects that artifact deliberately, and never claims installed-origin proof.
"""

from __future__ import annotations

import argparse
from contextlib import contextmanager
import hashlib
import json
import os
from pathlib import Path
import sys
import types
from typing import Any, Iterator

ROOT = Path(__file__).resolve().parents[1]
PIN_PATH = ROOT / "specs" / "gnn-pin.json"
REPOSITORY = "ActiveInferenceInstitute/Generalized_Notation_Notation"
COMMIT = "75c834bd8519dc7b5adc4d24f16bf393cfd1ecdf"
TAG = "v5.1.0"
BOOTSTRAP_SHA256 = "f638d4c01fe7de31e43d793e59bf382d0c3d1a82f365c59238334a2b40adfb37"
MANIFEST_SHA256 = "43b33c0b2b40386afa3f306fec4cc13bc1fd7c3b570fbf11d5008bad5c8e6b51"


class Unavailable(RuntimeError):
    """Required source admission or its selected runtime is unavailable."""


def add_arguments(parser: argparse.ArgumentParser) -> None:
    parser.add_argument(
        "--gnn-bootstrap", type=Path, default=os.environ.get("GNN_BOOTSTRAP"),
        help="independently reviewed bootstrap file ($GNN_BOOTSTRAP)",
    )
    parser.add_argument(
        "--gnn-source-manifest", type=Path, default=os.environ.get("GNN_SOURCE_MANIFEST"),
        help="independently frozen complete v5.1.0 manifest ($GNN_SOURCE_MANIFEST)",
    )
    parser.add_argument(
        "--gnn-origin-mode", choices=("installed", "source"),
        default=os.environ.get("GNN_ORIGIN_MODE", "installed"),
        help="installed VCS origin, or deliberately selected source artifact",
    )
    parser.add_argument(
        "--gnn-package-root", type=Path, default=os.environ.get("GNN_PACKAGE_ROOT"),
        help="expected gnn package directory; required in source mode",
    )


def command_arguments(args: argparse.Namespace) -> list[str]:
    """Freeze the parent's explicit resource/mode selection for a child."""
    result = ["--gnn-origin-mode", args.gnn_origin_mode]
    for name in ("gnn_bootstrap", "gnn_source_manifest", "gnn_package_root"):
        value = getattr(args, name)
        if value is not None:
            result.extend(("--" + name.replace("_", "-"), str(Path(value).absolute())))
    return result


def _checked_bytes(path: Path | None, expected: str, name: str) -> bytes:
    if path is None:
        raise Unavailable(f"{name} is required; select the independently reviewed resource")
    try:
        data = Path(path).read_bytes()
    except OSError as exc:
        raise Unavailable(f"{name} cannot be read: {exc}") from exc
    if hashlib.sha256(data).hexdigest() != expected:
        raise Unavailable(f"{name} SHA-256 mismatch (expected {expected})")
    return data


def load_bootstrap(path: Path | None) -> types.ModuleType:
    """Compile and execute the SAME checked bytes under a non-gnn identity.

    Do not use exec_module/run_path here: either can reread a replaced file or
    admit cached bytecode after the digest check.
    """
    data = _checked_bytes(path, BOOTSTRAP_SHA256, "GNN_BOOTSTRAP")
    name = "_actinf_rxinfer_reviewed_gnn_bootstrap"
    module = types.ModuleType(name)
    module.__file__ = str(Path(path).absolute())
    sys.modules[name] = module  # dataclasses resolves this non-gnn module name
    try:
        exec(compile(data, module.__file__, "exec", dont_inherit=True), module.__dict__)
    except BaseException:
        sys.modules.pop(name, None)
        raise
    return module


def _read_pin(bootstrap: types.ModuleType, path: Path) -> Any:
    pin = bootstrap.read_pin(path)
    if (pin.repository, pin.commit, pin.tag) != (REPOSITORY, COMMIT, TAG):
        raise Unavailable("source-pin-mismatch: the reviewed resources bind only the current v5.1.0 pin")
    if not pin.raw.get("language_version") or not pin.raw.get("parser_files"):
        raise Unavailable("the model pin requires language_version and parser_files")
    return pin


def pin_record(pin: Any) -> dict[str, Any]:
    """Return data only, using the producer's one pin normalizer."""
    return {
        "path": str(pin.path), "schema": pin.schema, "repository": pin.repository,
        "tag": pin.tag, "commit": pin.commit, "recorded": pin.recorded,
        "language_version": pin.raw.get("language_version"),
        "spec_files": list(pin.spec_files), "parser_files": pin.raw.get("parser_files"),
    }


def read_pin(args: argparse.Namespace) -> dict[str, Any]:
    bootstrap = load_bootstrap(args.gnn_bootstrap)
    # Pin data can select an installation source in run.sh. Require both
    # independent resources before that caller may mutate its runtime cache.
    _checked_bytes(args.gnn_source_manifest, MANIFEST_SHA256, "GNN_SOURCE_MANIFEST")
    try:
        result = pin_record(_read_pin(bootstrap, args.pin))
    except bootstrap.PinError as exc:
        raise Unavailable(str(exc)) from exc
    _checked_bytes(args.gnn_bootstrap, BOOTSTRAP_SHA256, "GNN_BOOTSTRAP")
    _checked_bytes(args.gnn_source_manifest, MANIFEST_SHA256, "GNN_SOURCE_MANIFEST")
    return result


@contextmanager
def _inputs(args: argparse.Namespace) -> Iterator[tuple[Any, Any, bytes, Path | None]]:
    bootstrap = load_bootstrap(args.gnn_bootstrap)
    try:
        pin = _read_pin(bootstrap, args.pin)
        manifest = _checked_bytes(args.gnn_source_manifest, MANIFEST_SHA256, "GNN_SOURCE_MANIFEST")
        package_root = args.gnn_package_root
        if args.gnn_origin_mode not in ("installed", "source"):
            raise Unavailable("GNN_ORIGIN_MODE must be installed or source")
        if args.gnn_origin_mode == "source" and package_root is None:
            raise Unavailable("source mode requires an explicit GNN_PACKAGE_ROOT/--gnn-package-root")
        previous_path = sys.path[:]
        try:
            if args.gnn_origin_mode == "source":
                # Only explicit source mode selects a source path. Installed
                # failures never retry here or fall back to GNN_ROOT.
                package_root = Path(package_root).absolute()
                if package_root.name != "gnn":
                    raise Unavailable("GNN_PACKAGE_ROOT must name the gnn package directory")
                sys.path.insert(0, str(package_root.parent))
            yield bootstrap, pin, manifest, package_root
        finally:
            sys.path[:] = previous_path
        _checked_bytes(args.gnn_bootstrap, BOOTSTRAP_SHA256, "GNN_BOOTSTRAP")
        _checked_bytes(args.gnn_source_manifest, MANIFEST_SHA256, "GNN_SOURCE_MANIFEST")
    except (bootstrap.PinError, bootstrap.SourceQualificationError, ImportError, OSError) as exc:
        code = getattr(exc, "code", "source-verdict-unavailable")
        raise Unavailable(f"{code}: {exc}") from exc


@contextmanager
def qualified_runtime(args: argparse.Namespace) -> Iterator[dict[str, Any]]:
    """Keep all GNN imports AND verdict execution inside this lifetime.

    The caller may retain only JSON-ready data. A fresh process is required for
    each verdict; the producer refuses already-imported GNN modules.
    """
    with _inputs(args) as (bootstrap, pin, manifest, package_root):
        with bootstrap.qualified_source(
            pin, manifest=manifest, manifest_sha256=MANIFEST_SHA256,
            package_root=package_root, origin_mode=args.gnn_origin_mode,
        ) as qualification:
            yield qualification


def check_importer(args: argparse.Namespace) -> dict[str, Any]:
    with _inputs(args) as (bootstrap, _pin, manifest, package_root):
        # The producer owns the checker and its qualified_source lifetime,
        # including exit revalidation. No consumer validator or static receipt.
        report = bootstrap.check_importer(
            args.repo, expected_commit=COMMIT, expected_tag=TAG,
            expected_repository=REPOSITORY, pin_path=args.pin,
            require_pointer=args.require_pointer, pointer_workflow=args.workflow,
            pointer_job=args.job, source_manifest=manifest,
            source_manifest_sha256=MANIFEST_SHA256, package_root=package_root,
            origin_mode=args.gnn_origin_mode,
        )
    return report


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("operation", choices=("pin", "check"))
    parser.add_argument("--pin", type=Path, default=PIN_PATH)
    parser.add_argument("--repo", type=Path, default=ROOT)
    parser.add_argument("--require-pointer", action="store_true")
    parser.add_argument("--workflow")
    parser.add_argument("--job")
    add_arguments(parser)
    args = parser.parse_args(argv)
    try:
        result = read_pin(args) if args.operation == "pin" else check_importer(args)
    except Unavailable as exc:
        print(f"gnn source admission not run: {exc}", file=sys.stderr)
        return 2
    # Publish only after all producer and resource exit revalidation succeeds.
    print(json.dumps(result, sort_keys=True))
    if args.operation == "pin":
        return 0
    if result["ok"] and result["qualified"]:
        return 0
    return 2 if result["source_qualification"]["status"] == "failed" else 1


if __name__ == "__main__":
    raise SystemExit(main())
