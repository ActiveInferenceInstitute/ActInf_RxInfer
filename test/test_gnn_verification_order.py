"""Real-file/process controls for the current-pin source-admission cutover.

Requires the reviewed GNN_BOOTSTRAP and GNN_SOURCE_MANIFEST, plus an explicit
GNN_RUNTIME_PYTHON with the parser dependencies. GNN_PACKAGE_ROOT may select
the reviewed source artifact; otherwise its package is located without import
in the selected runtime. Each test copies actual producer files into disposable
storage. No fake GNN modules, installed metadata, native results or network.
"""

from __future__ import annotations

import hashlib
import json
import os
from pathlib import Path
import shutil
import subprocess
import sys
import tempfile
import textwrap
import unittest

ROOT = Path(__file__).resolve().parents[1]
SOURCE = ROOT / "scripts" / "gnn_source.py"
PROBE = ROOT / "scripts" / "gnn_parser_probe.py"
VALIDATOR = ROOT / "scripts" / "validate_gnn_spec.py"
PIN = ROOT / "specs" / "gnn-pin.json"
SPEC = ROOT / "specs" / "coin_flip.gnn.md"
BOOTSTRAP_SHA256 = "f638d4c01fe7de31e43d793e59bf382d0c3d1a82f365c59238334a2b40adfb37"
MANIFEST_SHA256 = "43b33c0b2b40386afa3f306fec4cc13bc1fd7c3b570fbf11d5008bad5c8e6b51"


class GNNAdmissionTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        required = ("GNN_BOOTSTRAP", "GNN_SOURCE_MANIFEST", "GNN_RUNTIME_PYTHON")
        missing = [name for name in required if not os.environ.get(name)]
        if missing:
            raise RuntimeError("real GNN admission controls require " + ", ".join(missing))
        cls.bootstrap_bytes = Path(os.environ["GNN_BOOTSTRAP"]).read_bytes()
        cls.manifest_bytes = Path(os.environ["GNN_SOURCE_MANIFEST"]).read_bytes()
        for data, digest in (
            (cls.bootstrap_bytes, BOOTSTRAP_SHA256),
            (cls.manifest_bytes, MANIFEST_SHA256),
        ):
            if hashlib.sha256(data).hexdigest() != digest:
                raise RuntimeError("the test inputs are not the independently reviewed resources")
        selected = os.environ["GNN_RUNTIME_PYTHON"]
        cls.runtime = str(Path(shutil.which(selected) or selected).absolute())
        if os.environ.get("GNN_PACKAGE_ROOT"):
            cls.template = Path(os.environ["GNN_PACKAGE_ROOT"])
        else:
            located = subprocess.run(
                [
                    cls.runtime, "-P", "-c",
                    "import importlib.util,json; s=importlib.util.find_spec('gnn'); "
                    "print(json.dumps(s.origin if s else None))",
                ],
                stdin=subprocess.DEVNULL, capture_output=True, text=True, timeout=30,
            )
            if located.returncode != 0 or not json.loads(located.stdout):
                raise RuntimeError("cannot locate actual producer source: " + located.stderr)
            cls.template = Path(json.loads(located.stdout)).parent
        if not cls.template.is_dir():
            raise RuntimeError("GNN_PACKAGE_ROOT must select the real reviewed package")
        cls.pin = json.loads(PIN.read_text(encoding="utf-8"))

    def setUp(self):
        directory = tempfile.TemporaryDirectory(prefix="actinf-gnn-admission-")
        self.addCleanup(directory.cleanup)
        self.work = Path(directory.name)
        self.package = self.work / "source" / "gnn"
        shutil.copytree(
            self.template, self.package,
            ignore=shutil.ignore_patterns("__pycache__", "*.pyc", "*.pyo"),
        )
        self.bootstrap = self.work / "gnn_bootstrap.py"
        self.bootstrap.write_bytes(self.bootstrap_bytes)
        self.manifest = self.work / "source-manifest.json"
        self.manifest.write_bytes(self.manifest_bytes)
        self.marker = self.work / "unchecked-execution"

    def environment(self, **extra):
        env = {
            key: value for key, value in os.environ.items()
            if not key.startswith(("GNN_", "JULIA", "ACTINF_", "PYTHON"))
            and key not in ("BASH_ENV", "ENV", "VIRTUAL_ENV")
        }
        env.update(
            GNN_BOOTSTRAP=str(self.bootstrap),
            GNN_SOURCE_MANIFEST=str(self.manifest),
            GNN_ORIGIN_MODE="source",
            GNN_PACKAGE_ROOT=str(self.package),
            GNN_RUNTIME_PYTHON=self.runtime,
            PYTHONDONTWRITEBYTECODE="1",
        )
        env.update(extra)
        return env

    def run_process(self, command, *, env=None, cwd=None):
        return subprocess.run(
            command, cwd=cwd or self.work, env=env or self.environment(),
            stdin=subprocess.DEVNULL, capture_output=True, text=True, timeout=120,
        )

    def entry(self, name, *, env=None, pin=PIN, runtime=None, explicit_runtime=True, cwd=None):
        runtime = runtime or self.runtime
        if name == "validator":
            command = [
                sys.executable, "-P", str(VALIDATOR), "--pin", str(pin),
                "--receipt", str(self.work / "validator.json"), "--json",
            ]
            if explicit_runtime:
                command.extend(("--gnn-runtime", runtime))
        elif name == "probe":
            command = [
                runtime, "-P", str(PROBE), "--pin", str(pin), "--spec", str(SPEC),
                "--output", str(self.work / "probe.json"),
            ]
        elif name in ("pin", "check"):
            command = [runtime, "-P", str(SOURCE), name, "--pin", str(pin)]
            if name == "check":
                command.extend((
                    "--repo", str(ROOT), "--require-pointer",
                    "--workflow", ".github/workflows/ci.yml", "--job", "gnn-conformance",
                ))
        elif name == "gate":
            command = ["bash", str(ROOT / "run.sh"), "gnn"]
        else:
            raise AssertionError(name)
        return self.run_process(command, env=env, cwd=cwd)

    def assert_refused(self, completed, detail):
        output = completed.stdout + completed.stderr
        self.assertEqual(completed.returncode, 2, output)
        self.assertIn(detail, output)
        self.assertFalse(self.marker.exists(), output)

    def marker_code(self):
        return (
            "\nfrom pathlib import Path as _UncheckedPath\n"
            f"_UncheckedPath({str(self.marker)!r}).write_text('unchecked')\n"
        ).encode()

    def snippet(self, body, *, env=None):
        header = f"""\
import argparse
import importlib.util
import json
from pathlib import Path
import sys

spec = importlib.util.spec_from_file_location("admission_adapter", {str(SOURCE)!r})
source = importlib.util.module_from_spec(spec)
sys.modules[spec.name] = source
spec.loader.exec_module(source)
parser = argparse.ArgumentParser()
parser.add_argument("--pin", type=Path, default=Path({str(PIN)!r}))
source.add_arguments(parser)
admission = parser.parse_args([])
package = Path({str(self.package)!r})
document = Path({str(SPEC)!r})
"""
        program = header + "\ntry:\n" + textwrap.indent(textwrap.dedent(body), "    ")
        program += "\nexcept source.Unavailable as exc:\n    print(str(exc), file=sys.stderr)\n    sys.exit(2)\n"
        return self.run_process([self.runtime, "-P", "-c", program], env=env)

    def test_every_entry_refuses_unchecked_bootstrap_before_any_gnn_execution(self):
        self.bootstrap.write_bytes(self.bootstrap_bytes + self.marker_code())
        init = self.package / "__init__.py"
        init.write_bytes(init.read_bytes() + self.marker_code())
        for entry in ("pin", "probe", "check", "validator", "gate"):
            with self.subTest(entry=entry):
                self.assert_refused(self.entry(entry), "GNN_BOOTSTRAP SHA-256 mismatch")

    def test_unadmitted_resources_cannot_start_provisioning_or_invalidate_readiness(self):
        tools = self.work / "tools"
        tools.mkdir()
        uv = tools / "uv"
        uv.write_text(
            f"#!{sys.executable}\nfrom pathlib import Path\n"
            f"Path({str(self.marker)!r}).write_text('unadmitted installer')\n"
            "raise SystemExit(97)\n",
            encoding="utf-8",
        )
        uv.chmod(0o755)
        cache = self.work / "cache"
        marker = cache / "gnn-runtime" / ".pin-commit"
        marker.parent.mkdir(parents=True)
        marker.write_text(self.pin["commit"] + "\n", encoding="utf-8")
        for resource, detail in (
            (self.bootstrap, "GNN_BOOTSTRAP"), (self.manifest, "GNN_SOURCE_MANIFEST"),
        ):
            with self.subTest(resource=detail):
                self.bootstrap.write_bytes(self.bootstrap_bytes)
                self.manifest.write_bytes(self.manifest_bytes)
                resource.write_bytes(resource.read_bytes() + b" ")
                env = self.environment(
                    PYTHON=sys.executable, GNN_ORIGIN_MODE="installed",
                    ACTINF_GATE_DIR=str(cache),
                    PATH=str(tools) + os.pathsep + os.environ.get("PATH", ""),
                )
                env.pop("GNN_RUNTIME_PYTHON")
                self.assert_refused(self.entry("gate", env=env), detail + " SHA-256 mismatch")
                self.assertEqual(marker.read_text(), self.pin["commit"] + "\n")

    def test_bootstrap_executes_the_checked_bytes_not_a_second_file_read(self):
        # Replace before a second source read OR at compile after the checked
        # read. A loader that rereads now gets malicious bytes; compile(data)
        # must still execute the already-checked real producer.
        completed = self.snippet(f"""
            reads = 0
            replaced = False
            def replace_before_unchecked_use(event, arguments):
                global reads, replaced
                selected = str(admission.gnn_bootstrap.absolute())
                trigger = event == "compile" and arguments[1] == selected
                if event == "open" and arguments[0] == selected and arguments[1] in ("r", "rb"):
                    reads += 1
                    trigger = reads > 1
                if trigger and not replaced:
                    replaced = True
                    admission.gnn_bootstrap.write_bytes({self.marker_code()!r})
            sys.addaudithook(replace_before_unchecked_use)
            bootstrap = source.load_bootstrap(admission.gnn_bootstrap)
            print(json.dumps(source.pin_record(bootstrap.read_pin(admission.pin))))
        """)
        self.assertEqual(completed.returncode, 0, completed.stdout + completed.stderr)
        self.assertEqual(json.loads(completed.stdout)["commit"], self.pin["commit"])
        self.assertFalse(self.marker.exists())

    def test_cached_bootstrap_bytecode_cannot_replace_checked_source(self):
        completed = self.snippet(f"""
            import os
            import py_compile
            original = admission.gnn_bootstrap.read_bytes()
            replacement = {self.marker_code()!r}
            assert len(replacement) < len(original)
            admission.gnn_bootstrap.write_bytes(replacement + b"#" * (len(original) - len(replacement)))
            stamp = admission.gnn_bootstrap.stat()
            py_compile.compile(str(admission.gnn_bootstrap), doraise=True)
            admission.gnn_bootstrap.write_bytes(original)
            os.utime(admission.gnn_bootstrap, ns=(stamp.st_atime_ns, stamp.st_mtime_ns))
            bootstrap = source.load_bootstrap(admission.gnn_bootstrap)
            print(json.dumps(source.pin_record(bootstrap.read_pin(admission.pin))))
        """)
        self.assertEqual(completed.returncode, 0, completed.stdout + completed.stderr)
        self.assertEqual(json.loads(completed.stdout)["commit"], self.pin["commit"])
        self.assertFalse(self.marker.exists())

    def test_importing_the_consumer_probe_does_not_execute_gnn(self):
        completed = self.snippet(f"""
            spec = importlib.util.spec_from_file_location("consumer_probe", {str(PROBE)!r})
            probe = importlib.util.module_from_spec(spec)
            sys.modules[spec.name] = probe
            spec.loader.exec_module(probe)
            loaded = [name for name in sys.modules if name == "gnn" or name.startswith("gnn.")]
            print(json.dumps(loaded))
        """)
        self.assertEqual(completed.returncode, 0, completed.stdout + completed.stderr)
        self.assertEqual(json.loads(completed.stdout), [])

    def test_every_verdict_refuses_corrupt_independent_manifest(self):
        self.manifest.write_bytes(self.manifest_bytes + b" ")
        init = self.package / "__init__.py"
        init.write_bytes(init.read_bytes() + self.marker_code())
        for entry in ("pin", "probe", "check", "validator", "gate"):
            with self.subTest(entry=entry):
                self.assert_refused(self.entry(entry), "GNN_SOURCE_MANIFEST SHA-256 mismatch")

    def test_full_manifest_protects_verdict_code_not_in_the_legacy_pin(self):
        relative = "validation/consistency_checker.py"
        self.assertNotIn("src/gnn/" + relative, self.pin["parser_files"])
        member = self.package / relative
        member.write_bytes(member.read_bytes() + self.marker_code())
        for entry in ("probe", "check", "validator"):
            with self.subTest(entry=entry):
                self.assert_refused(self.entry(entry), "source-content-mismatch")

    def test_missing_and_extra_package_members_are_not_a_partial_manifest_pass(self):
        member = self.package / "validation" / "consistency_checker.py"
        original = member.read_bytes()
        for mutation in ("missing", "extra"):
            with self.subTest(mutation=mutation):
                extra = self.package / "unreviewed.py"
                if mutation == "missing":
                    member.unlink()
                else:
                    extra.write_bytes(self.marker_code())
                try:
                    for entry in ("probe", "check"):
                        self.assert_refused(self.entry(entry), "source-content-mismatch")
                finally:
                    member.write_bytes(original)
                    extra.unlink(missing_ok=True)

    def test_recorded_parser_digest_remains_required_by_the_producer(self):
        altered = json.loads(PIN.read_text(encoding="utf-8"))
        altered["parser_files"]["src/gnn/__init__.py"] = "0" * 64
        pin = self.work / "altered-pin.json"
        pin.write_text(json.dumps(altered), encoding="utf-8")
        self.assert_refused(self.entry("probe", pin=pin), "source-parser-digest-mismatch")

    def test_probe_checker_and_validator_publish_only_exit_qualified_real_results(self):
        for entry in ("probe", "check", "validator"):
            with self.subTest(entry=entry):
                completed = self.entry(entry)
                self.assertEqual(completed.returncode, 0, completed.stdout + completed.stderr)
                if entry == "check":
                    payload = json.loads(completed.stdout)
                    self.assertTrue(payload["qualified"])
                    self.assertEqual(payload["specs"]["invalid"], [])
                    self.assertIn("specs/coin_flip.gnn.md", payload["specs"]["files"])
                    self.assertEqual(payload["specs"]["validated"], payload["specs"]["count"])
                else:
                    payload = json.loads((self.work / f"{entry}.json").read_text())
                    self.assertTrue(payload["parser"]["success"] if entry == "probe" else payload["parser_success"])
                    self.assertEqual(Path(payload["gnn_module"]).resolve().parent, self.package)
                qualification = payload["source_qualification"]
                self.assertTrue(qualification["ok"])
                self.assertTrue(qualification["imports_verified"])
                self.assertTrue(qualification["preimport"])
                self.assertEqual(qualification["status"], "qualified")
                self.assertEqual(qualification["commit"], self.pin["commit"])
                self.assertEqual(qualification["manifest_sha256"], MANIFEST_SHA256)
                self.assertEqual(qualification["origin"]["kind"], "explicit-source")
                self.assertFalse(qualification["origin"]["vcs_verified"])
                self.assertIn("gnn", qualification["loaded_modules"])

    def test_cwd_decoy_cannot_replace_the_explicitly_selected_package(self):
        decoy = self.work / "decoy" / "gnn"
        shutil.copytree(self.package, decoy)
        init = decoy / "__init__.py"
        init.write_bytes(init.read_bytes() + self.marker_code())
        completed = self.entry("probe", cwd=decoy.parent)
        self.assertEqual(completed.returncode, 0, completed.stdout + completed.stderr)
        payload = json.loads((self.work / "probe.json").read_text())
        self.assertTrue(payload["parser"]["success"])
        self.assertEqual(Path(payload["gnn_module"]).resolve().parent, self.package)
        self.assertFalse(self.marker.exists())

    def test_mutation_before_a_late_import_cannot_execute_changed_bytes(self):
        completed = self.snippet(f"""
            with source.qualified_runtime(admission):
                import gnn
                member = package / "parsers" / "markdown_parser.py"
                member.write_bytes(member.read_bytes() + {self.marker_code()!r})
                from gnn.parsers.markdown_parser import MarkdownGNNParser
            print("unqualified success")
        """)
        self.assert_refused(completed, "source-content-mismatch")
        self.assertNotIn("unqualified success", completed.stdout)

    def test_real_parse_cannot_escape_exit_inventory_revalidation(self):
        completed = self.snippet("""
            with source.qualified_runtime(admission):
                from gnn.parsers.markdown_parser import MarkdownGNNParser
                result = MarkdownGNNParser().parse_file(str(document))
                assert result.success, result.errors
                member = package / "validation" / "consistency_checker.py"
                member.write_bytes(member.read_bytes() + b"\\n# concurrent change\\n")
            print("unqualified success")
        """)
        self.assert_refused(completed, "source-content-mismatch")
        self.assertNotIn("unqualified success", completed.stdout)

    def test_loaded_module_origin_is_rechecked_at_scope_exit(self):
        completed = self.snippet("""
            with source.qualified_runtime(admission):
                import gnn
                gnn.__file__ = str(package / "elsewhere.py")
            print("unqualified success")
        """)
        self.assert_refused(completed, "source-loaded-module-mismatch")
        self.assertNotIn("unqualified success", completed.stdout)

    def test_resource_mutation_during_a_real_parse_is_not_published(self):
        completed = self.snippet("""
            with source.qualified_runtime(admission):
                from gnn.parsers.markdown_parser import MarkdownGNNParser
                result = MarkdownGNNParser().parse_file(str(document))
                assert result.success, result.errors
                admission.gnn_source_manifest.write_bytes(b"{}")
            print("unqualified success")
        """)
        self.assert_refused(completed, "GNN_SOURCE_MANIFEST SHA-256 mismatch")
        self.assertNotIn("unqualified success", completed.stdout)

    def test_already_imported_real_gnn_is_not_retroactively_qualified(self):
        completed = self.snippet("""
            sys.path.insert(0, str(package.parent))
            import gnn
            with source.qualified_runtime(admission):
                print("unqualified success")
        """)
        self.assert_refused(completed, "source-already-imported")
        self.assertNotIn("unqualified success", completed.stdout)

    def forwarding_runtime(self, *, no_site=False):
        wrapper = self.work / ("runtime-no-site" if no_site else "selected-runtime")
        prefix = [self.runtime, "-S"] if no_site else [self.runtime]
        log = self.work / "selected-runtime.jsonl"
        wrapper.write_text(
            f"#!{sys.executable}\nimport json,os,sys\nfrom pathlib import Path\n"
            f"with Path({str(log)!r}).open('a') as out: out.write(json.dumps(sys.argv[1:]) + '\\n')\n"
            f"os.execv({self.runtime!r}, {prefix!r} + sys.argv[1:])\n",
            encoding="utf-8",
        )
        wrapper.chmod(0o755)
        return str(wrapper), log

    def test_missing_installed_origin_cannot_fall_back_to_available_source(self):
        # -S uses a real interpreter without site metadata, not fabricated
        # direct_url.json. The real package is import-resolvable via PYTHONPATH.
        runtime, _log = self.forwarding_runtime(no_site=True)
        env = self.environment(
            GNN_ORIGIN_MODE="installed", PYTHONPATH=str(self.package.parent),
            GNN_ROOT=str(self.template.parent.parent),
        )
        for entry in ("probe", "check", "validator"):
            with self.subTest(entry=entry):
                self.assert_refused(
                    self.entry(entry, runtime=runtime, env=env), "source-origin-unavailable"
                )
        self.assertFalse((self.work / "validator.json").exists())

    def test_source_mode_requires_an_explicit_package_not_the_provisioning_checkout(self):
        env = self.environment(GNN_ROOT=str(self.template.parent.parent))
        env.pop("GNN_PACKAGE_ROOT")
        self.assert_refused(self.entry("probe", env=env), "requires an explicit GNN_PACKAGE_ROOT")

    def test_an_unavailable_selected_runtime_is_not_replaced_by_the_host_or_checkout(self):
        env = self.environment(
            GNN_RUNTIME_PYTHON=str(self.work / "absent-python"),
            GNN_ROOT=str(self.template.parent.parent),
        )
        completed = self.entry("validator", env=env, explicit_runtime=False)
        self.assert_refused(completed, "absent-python")
        self.assertFalse((self.work / "validator.json").exists())

    def test_cli_runtime_overrides_environment_for_both_pin_and_real_verdict(self):
        runtime, log = self.forwarding_runtime()
        env = self.environment(GNN_RUNTIME_PYTHON=str(self.work / "absent-python"))
        completed = self.entry("validator", runtime=runtime, env=env)
        self.assertEqual(completed.returncode, 0, completed.stdout + completed.stderr)
        receipt = json.loads((self.work / "validator.json").read_text())
        self.assertTrue(receipt["ok"])
        self.assertTrue(receipt["parser_success"])
        self.assertTrue(receipt["source_qualification"]["imports_verified"])
        self.assertEqual(Path(receipt["gnn_module"]).resolve().parent, self.package)
        launches = [json.loads(line) for line in log.read_text().splitlines()]
        self.assertEqual(
            [Path(args[1]).name for args in launches],
            ["gnn_source.py", "gnn_parser_probe.py"],
        )
        self.assertTrue(all(args[0] == "-P" for args in launches))


if __name__ == "__main__":
    unittest.main()
