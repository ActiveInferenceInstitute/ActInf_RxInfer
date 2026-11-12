"""Offline tests for the pin-binding checks in ``scripts/validate_gnn_spec.py``.

Standard library only, and no network: remote tag resolution is exercised
against a stubbed ``git ls-remote``, and the runtime is a stub. Run with
``python3 -m unittest discover -s test -p 'test_*.py'`` (``./run.sh gnn`` does).
"""

from __future__ import annotations

import contextlib
import importlib.util
import io
import json
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path
from unittest import mock

ROOT = Path(__file__).resolve().parents[1]
COMMIT = "a" * 40
OTHER = "b" * 40


def _load():
    spec = importlib.util.spec_from_file_location(
        "validate_gnn_spec_under_test", ROOT / "scripts" / "validate_gnn_spec.py"
    )
    module = importlib.util.module_from_spec(spec)
    sys.modules[spec.name] = module
    spec.loader.exec_module(module)
    return module


vgs = _load()


def _pin(**overrides):
    pin = {
        "repository": "https://example.invalid/Generalized_Notation_Notation",
        "tag": "v9.9.9",
        "commit": COMMIT,
        "language_version": "GNN v1.1",
        "parser_files": {"src/gnn/__init__.py": "0" * 64},
    }
    pin.update(overrides)
    return pin


def _ls_remote(stdout, returncode=0):
    def fake_run(command, **_kwargs):
        return subprocess.CompletedProcess(command, returncode, stdout=stdout, stderr="boom")

    return mock.patch.object(vgs.subprocess, "run", fake_run)


class TagBindingTests(unittest.TestCase):
    def test_offline_is_explicitly_unresolved_and_uses_no_network(self):
        with mock.patch.object(vgs.subprocess, "run", side_effect=AssertionError("network")):
            binding = vgs.tag_binding(_pin())
        self.assertEqual(binding["status"], "unresolvable-offline")
        self.assertIsNone(binding["resolved"])
        self.assertEqual(vgs.tag_failures(binding, _pin()), [])

    def test_remote_prefers_the_peeled_commit_of_an_annotated_tag(self):
        listing = f"{OTHER}\trefs/tags/v9.9.9\n{COMMIT}\trefs/tags/v9.9.9^{{}}\n"
        with _ls_remote(listing):
            binding = vgs.tag_binding(_pin(), remote=True)
        self.assertEqual(binding["status"], "verified")
        self.assertEqual(binding["resolved"], COMMIT)
        self.assertEqual(vgs.tag_failures(binding, _pin()), [])

    def test_a_tag_resolving_elsewhere_fails_by_name(self):
        with _ls_remote(f"{OTHER}\trefs/tags/v9.9.9\n"):
            binding = vgs.tag_binding(_pin(), remote=True)
        failures = vgs.tag_failures(binding, _pin())
        self.assertEqual(len(failures), 1)
        self.assertTrue(failures[0].startswith(vgs.TAG_COMMIT_MISMATCH))

    def test_look_alike_tags_do_not_match(self):
        with _ls_remote(f"{OTHER}\trefs/tags/v9.9.9-rc1\n"):
            binding = vgs.tag_binding(_pin(), remote=True)
        self.assertEqual(binding["status"], "unresolvable-offline")
        self.assertIn("not listed", binding["detail"])

    def test_a_failed_remote_is_unresolved_never_a_pass(self):
        with _ls_remote("", returncode=128):
            binding = vgs.tag_binding(_pin(), remote=True)
        self.assertEqual(binding["status"], "unresolvable-offline")
        self.assertIn("ls-remote failed", binding["detail"])


class RemoteUrlTests(unittest.TestCase):
    def test_owner_name_pins_become_github_urls(self):
        self.assertEqual(
            vgs.remote_url("ActiveInferenceInstitute/Generalized_Notation_Notation"),
            "https://github.com/ActiveInferenceInstitute/Generalized_Notation_Notation",
        )
        self.assertEqual(vgs.remote_url("https://example.invalid/x"), "https://example.invalid/x")

    def test_ls_remote_receives_the_full_url_for_a_normalized_pin(self):
        seen = []

        def fake_run(command, **_kwargs):
            seen.append(command)
            return subprocess.CompletedProcess(command, 0, stdout="", stderr="")

        with mock.patch.object(vgs.subprocess, "run", fake_run):
            vgs.tag_binding(_pin(repository="Org/Repo"), remote=True)
        self.assertIn("https://github.com/Org/Repo", seen[0])


class RevisionTests(unittest.TestCase):
    def test_installed_commit_must_match_the_pin(self):
        pin = _pin()
        self.assertEqual(vgs.revision_failures({"status": "verified", "commit": COMMIT}, pin), [])
        self.assertEqual(vgs.revision_failures({"status": "unresolvable-offline"}, pin), [])
        mismatch = vgs.revision_failures({"status": "verified", "commit": OTHER}, pin)
        self.assertTrue(mismatch[0].startswith(vgs.TAG_COMMIT_MISMATCH))
        conflict = vgs.revision_failures({"status": "conflicting", "detail": "two"}, pin)
        self.assertTrue(conflict[0].startswith(vgs.TAG_COMMIT_MISMATCH))


class LanguageVersionTests(unittest.TestCase):
    def test_normalization(self):
        for text in ("GNN v1.1", "v1.1", "1.1", "GNN v1.1 + flags"):
            self.assertEqual(vgs.normalize_language_version(text), "1.1")
        self.assertIsNone(vgs.normalize_language_version("latest"))

    def test_the_committed_document_matches_the_committed_pin(self):
        spec = (ROOT / "specs" / "coin_flip.gnn.md").read_text(encoding="utf-8")
        pin = json.loads((ROOT / "specs" / "gnn-pin.json").read_text(encoding="utf-8"))
        self.assertEqual(
            vgs.language_version_failures(
                pin, document=vgs.document_language_version(spec), parser="1.1"
            ),
            [],
        )

    def test_document_or_parser_disagreeing_with_the_pin_fails(self):
        failures = vgs.language_version_failures(_pin(), document="1.0", parser="2.0")
        self.assertEqual(len(failures), 2)
        self.assertTrue(all(f.startswith(vgs.LANGUAGE_VERSION_MISMATCH) for f in failures))
        self.assertEqual(
            len(vgs.language_version_failures(_pin(), document="1.1", parser="1.0")), 1
        )

    def test_document_language_version_reads_the_section(self):
        self.assertEqual(
            vgs.document_language_version("## GNNVersionAndFlags\n\nGNN v1.1\n\n## ModelName\n"),
            "1.1",
        )
        self.assertIsNone(vgs.document_language_version("## ModelName\n\nx\n"))


class MainOrderingTests(unittest.TestCase):
    """Drive ``main`` with a stub runtime; the parser must never run first."""

    def _run(self, *extra, tag_listing=None, package=None):
        probed = []

        def fake_probe(*_args, **_kwargs):
            probed.append("probe")
            raise AssertionError("the parser must not run before the digests verify")

        with tempfile.TemporaryDirectory() as directory:
            directory = Path(directory)
            patches = [
                mock.patch.object(vgs, "read_pin", lambda *_a, **_k: _pin()),
                mock.patch.object(vgs, "run_probe", fake_probe),
                mock.patch.object(vgs, "locate_package", lambda *_a, **_k: package),
            ]
            if tag_listing is not None:
                patches.append(_ls_remote(*tag_listing))
            stderr = io.StringIO()
            with contextlib.ExitStack() as stack:
                for patch in patches:
                    stack.enter_context(patch)
                with contextlib.redirect_stderr(stderr):
                    code = vgs.main(
                        [
                            "--gnn-runtime",
                            sys.executable,
                            "--receipt",
                            str(directory / "receipt.json"),
                            *extra,
                        ]
                    )
        return code, probed, stderr.getvalue()

    def test_digest_mismatch_is_not_run_before_parsing(self):
        with tempfile.TemporaryDirectory() as directory:
            package = Path(directory)
            (package / "__init__.py").write_text("tampered", encoding="utf-8")
            code, probed, err = self._run(package=package)
        self.assertEqual(code, 2)
        self.assertEqual(probed, [])
        self.assertIn("digest mismatch", err)

    def test_verify_tag_remote_that_cannot_answer_is_not_run(self):
        code, probed, err = self._run("--verify-tag-remote", tag_listing=("", 128))
        self.assertEqual(code, 2)
        self.assertEqual(probed, [])
        self.assertIn("--verify-tag-remote", err)


if __name__ == "__main__":
    unittest.main()
