"""Ordering tests for the pinned GNN runtime, end to end.

Two properties are asserted, both about *when* the installed parser may run and
*which* copy of it runs:

1. ``./run.sh gnn`` must verify the installed parser digests before the shared
   ``gnn.importers check`` reader imports that parser and validates the document
   with it. The reader is now the second command of the arm for that reason.
2. The package the digests are verified against must be the package the probe
   parses with. ``python -c`` used to resolve ``gnn`` from the working directory
   while the probe, run as a file, resolved it from ``scripts/`` and the
   distribution; a stand-in package in the working directory therefore satisfied
   the digest check and the parse still ran elsewhere.

Standard library only and no network: the pinned runtime is this interpreter
with a stand-in ``gnn`` package on ``PYTHONPATH``, the stand-in pin reader
returns a fixed pin whose ``repository`` is a path that does not exist (so
``git ls-remote`` fails immediately), and every stand-in file that must not run
records itself when it does.

Run with ``python3 -m unittest discover -s test -p 'test_*.py'``
(``./run.sh gnn`` does).
"""

from __future__ import annotations

import hashlib
import json
import os
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
VALIDATOR = ROOT / "scripts" / "validate_gnn_spec.py"
COMMIT = "a" * 40

#: The pin the stand-in reader returns. ``parser_files`` is filled in per test.
PIN = {
    "schema": "gnn-importer-pin/v1",
    "repository": "/nonexistent/gnn",
    "tag": "v9.9.9",
    "commit": COMMIT,
    "language_version": "GNN v1.1",
    "recorded": "2026-01-01",
}

PACKAGE_FILES = (
    "__init__.py",
    "importers.py",
    "parsers/__init__.py",
    "parsers/markdown_parser.py",
)

INIT = '''\
"""Stand-in for the installed ``gnn`` package."""
import os
from pathlib import Path

__version__ = "9.9.9"

Path(os.environ["GNN_STANDIN_LOG"]).open("a").write("gnn\\n")
'''

IMPORTERS = '''\
"""Stand-in for ``gnn.importers``: only ``read_pin`` is reached here."""
import json
import os
from pathlib import Path


def _log(entry):
    Path(os.environ["GNN_STANDIN_LOG"]).open("a").write(entry + "\\n")


class _Pin:
    def __init__(self, path, data):
        self.path = Path(path)
        self.schema = data.get("schema")
        self.repository = data["repository"]
        self.tag = data["tag"]
        self.commit = data["commit"]
        self.recorded = data.get("recorded")
        self.raw = data
        self.spec_files = tuple(data.get("spec_files") or ())


def read_pin(path):
    _log("read_pin")
    return _Pin(path, json.loads(Path(os.environ["GNN_STANDIN_PIN"]).read_text()))


if __name__ == "__main__":
    _log("reader-step")
'''

MARKDOWN_PARSER = '''\
"""Stand-in for the pinned parser: importing it is what must not happen early."""
import os
from pathlib import Path

Path(os.environ["GNN_STANDIN_PARSED"]).write_text("markdown_parser imported\\n")
'''


def _env(**extra):
    """Return the environment for a nested gate run, without GNN/Julia overrides."""

    ignored = {"PYTHONPATH", "PYTHONSAFEPATH", "JULIA_BIN", "GNN_RUNTIME_PYTHON"}
    env = {name: value for name, value in os.environ.items() if name not in ignored}
    env.update(extra)
    return env


def _package(root: Path, *, tampered: bool = False) -> Path:
    """Write a stand-in ``gnn`` package under ``root`` and return it."""

    for relative in PACKAGE_FILES:
        path = root / "gnn" / relative
        path.parent.mkdir(parents=True, exist_ok=True)
        if relative == "__init__.py":
            body = INIT
        elif relative == "importers.py":
            body = IMPORTERS
        elif relative == "parsers/markdown_parser.py":
            body = MARKDOWN_PARSER
        else:
            body = ""
        if tampered:
            body += "# not the file the pin records\n"
        path.write_text(body, encoding="utf-8")
    return root / "gnn"


def _digests(package: Path) -> dict[str, str]:
    """Return the pin's ``src/gnn/...`` digest mapping for ``package``."""

    return {
        f"src/gnn/{relative}": hashlib.sha256(
            (package / relative).read_bytes()
        ).hexdigest()
        for relative in PACKAGE_FILES
    }


def _log(path: Path) -> list[str]:
    return path.read_text(encoding="utf-8").split() if path.exists() else []


class GateOrderingTests(unittest.TestCase):
    """``./run.sh gnn`` must verify digests before the reader imports the parser."""

    @unittest.skipIf(
        os.environ.get("ACTINF_GATE_NESTED"),
        "the gate runs this suite; nested runs are already covered",
    )
    def test_the_reader_does_not_import_the_parser_before_its_digests_verify(self):
        with tempfile.TemporaryDirectory() as directory:
            work = Path(directory)
            package = _package(work / "standin")
            pin = work / "pin.json"
            pin.write_text(
                json.dumps({**PIN, "parser_files": {"src/gnn/__init__.py": "0" * 64}}),
                encoding="utf-8",
            )
            log = work / "log"
            parsed = work / "parsed"
            completed = subprocess.run(
                ["bash", "run.sh", "gnn"],
                cwd=ROOT,
                timeout=300,
                capture_output=True,
                text=True,
                env=_env(
                    PYTHON=sys.executable,
                    GNN_RUNTIME_PYTHON=sys.executable,
                    PYTHONPATH=str(package.parent),
                    GNN_STANDIN_LOG=str(log),
                    GNN_STANDIN_PIN=str(pin),
                    GNN_STANDIN_PARSED=str(parsed),
                    ACTINF_GATE_NESTED="1",
                ),
            )
            entries = _log(log)
            parsed_exists = parsed.exists()

        output = f"stdout:\n{completed.stdout}\nstderr:\n{completed.stderr}"
        self.assertEqual(completed.returncode, 2, output)
        self.assertIn("read_pin", entries, output)
        self.assertNotIn(
            "reader-step",
            entries,
            "the shared reader ran before the digests were verified: " + output,
        )
        self.assertFalse(
            parsed_exists,
            "a parser file in the pinned package was imported before verification: " + output,
        )


class VerifiedPackageIsTheParsingPackageTests(unittest.TestCase):
    """The digests must be checked against the package the probe parses with."""

    def test_a_stand_in_gnn_in_the_working_directory_is_never_the_parsed_one(self):
        with tempfile.TemporaryDirectory() as directory:
            work = Path(directory)
            decoy = _package(work / "decoy")
            installed = _package(work / "installed", tampered=True)
            pin = work / "pin.json"
            pin.write_text(
                json.dumps({**PIN, "parser_files": _digests(decoy)}), encoding="utf-8"
            )
            log = work / "log"
            parsed = work / "parsed"
            completed = subprocess.run(
                [
                    sys.executable,
                    str(VALIDATOR),
                    "--gnn-runtime",
                    sys.executable,
                    "--pin",
                    str(pin),
                    "--receipt",
                    str(work / "receipt.json"),
                ],
                # The working directory holds a package whose digests match the
                # pin; the installed package on PYTHONPATH does not.
                cwd=decoy.parent,
                timeout=300,
                capture_output=True,
                text=True,
                env=_env(
                    PYTHONPATH=str(installed.parent),
                    GNN_STANDIN_LOG=str(log),
                    GNN_STANDIN_PIN=str(pin),
                    GNN_STANDIN_PARSED=str(parsed),
                ),
            )
            parsed_exists = parsed.exists()

        output = f"stdout:\n{completed.stdout}\nstderr:\n{completed.stderr}"
        self.assertEqual(completed.returncode, 2, output)
        self.assertIn("digest mismatch", completed.stderr, output)
        self.assertFalse(
            parsed_exists,
            "the probe parsed with a package the digests were not verified against: "
            + output,
        )


if __name__ == "__main__":
    unittest.main()
