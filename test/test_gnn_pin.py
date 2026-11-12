"""Dependency-free regression tests for the local GNN pin reader."""

from __future__ import annotations

import importlib.util
import json
import tempfile
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
MODULE_SPEC = importlib.util.spec_from_file_location(
    "validate_gnn_spec", ROOT / "scripts" / "validate_gnn_spec.py"
)
VALIDATOR = importlib.util.module_from_spec(MODULE_SPEC)
MODULE_SPEC.loader.exec_module(VALIDATOR)


class PinSchemaTests(unittest.TestCase):
    def setUp(self) -> None:
        self.pin = json.loads((ROOT / "specs" / "gnn-pin.json").read_text(encoding="utf-8"))
        self.directory = tempfile.TemporaryDirectory()
        self.addCleanup(self.directory.cleanup)
        self.path = Path(self.directory.name) / "pin.json"

    def write_pin(self) -> None:
        self.path.write_text(json.dumps(self.pin), encoding="utf-8")

    def test_committed_schema_is_accepted(self) -> None:
        self.write_pin()
        self.assertEqual(VALIDATOR.load_pin(self.path), self.pin)

    def test_missing_schema_is_rejected(self) -> None:
        del self.pin["schema"]
        self.write_pin()
        with self.assertRaisesRegex(VALIDATOR.Unavailable, "missing the 'schema' field"):
            VALIDATOR.load_pin(self.path)

    def test_malformed_schema_is_rejected(self) -> None:
        for schema in ("gnn-importer-pin/v2", "", None, 1, [], {}):
            with self.subTest(schema=schema):
                self.pin["schema"] = schema
                self.write_pin()
                with self.assertRaisesRegex(VALIDATOR.Unavailable, "unsupported schema"):
                    VALIDATOR.load_pin(self.path)


if __name__ == "__main__":
    unittest.main()
