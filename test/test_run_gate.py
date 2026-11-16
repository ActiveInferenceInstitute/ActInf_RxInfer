"""Command-fixture regressions for run.sh; standard library, no scientific work.

Each test copies the real gate into a temporary repository. Julia, uv, the GNN
runtime and filesystem commands are controlled executables; no download or
package import is possible. Measurement uses the real gate_report.py, but writes
only fixture receipts. These tests prove dispatch/cache behavior, not inference.
"""

from __future__ import annotations

import json
import os
from pathlib import Path
import shutil
import subprocess
import sys
import tempfile
import unittest

ROOT = Path(__file__).resolve().parents[1]
COMMIT = "a" * 40
OLD_COMMIT = "b" * 40
FAILURE = 41

COMMAND = r'''
import json
import os
from pathlib import Path
import shutil
import sys
import tempfile

name = Path(sys.argv[0]).name
args = sys.argv[1:]
work = Path(os.environ["GATE_FIXTURE_ROOT"])
runtime = work / "cache" / "gnn-runtime"
marker = runtime / ".pin-commit"
state = runtime / "state"
commit = os.environ["GATE_FIXTURE_COMMIT"]


def record(phase, **details):
    with (work / "commands.jsonl").open("a", encoding="utf-8") as log:
        log.write(json.dumps({"phase": phase, "marker": marker.exists(), **details}) + "\n")


def fail(phase):
    if os.environ.get("GATE_FIXTURE_FAIL") == phase:
        sys.exit(41)


if name == "host-python":
    if args[0] == "-c":
        field = "repository" if '["repository"]' in args[1] else "commit"
        phase = "pin-" + field
        record(phase)
        if os.environ.get("GATE_FIXTURE_FAIL") == phase:
            # Valid-looking stdout must never hide a failed pin read.
            print("https://example.invalid/gnn" if field == "repository" else commit)
            sys.exit(41)
        os.execv(sys.executable, [sys.executable, "-B", *args])
    if args[:2] == ["scripts/gnn_source.py", "pin"]:
        record("pin-admission")
        print(json.dumps({"repository": "example.invalid/gnn", "commit": commit}))
        fail("pin-admission")
        sys.exit(0)  # Command-dispatch fixture only; never parser evidence.
    if args[0] == "scripts/gate_report.py":
        os.execv(sys.executable, [sys.executable, "-B", *args])
    phases = {
        "scripts/lint.py": "lint",
        "scripts/check_links.py": "links",
        "scripts/validate_gnn_spec.py": "validator",
    }
    if args[0] in phases:
        record(phases[args[0]])
        fail(phases[args[0]])
    elif args[:2] == ["-m", "unittest"]:
        record("unit-tests")  # Do not recursively discover this fixture suite.
    else:
        sys.exit("unexpected host Python command: " + repr(args))
elif name == "julia":
    if args == ["--version"]:
        print("fixture Julia (no scientific runtime)")
    else:
        arm = os.environ.get("ACTINF_RXINFER_TEST_ARM", "full")
        record("julia-tests", arm=arm)
        print("ActInf_RxInfer | " + ("0 2 2" if arm == "fast" else "2 2"))
elif name == "uv":
    if args == ["--version"]:
        print("fixture uv (no installer)")
    elif args[0] == "venv":
        record("venv")
        (runtime / "bin").mkdir(parents=True, exist_ok=True)
        shutil.copy2(__file__, runtime / "bin" / "python")
        state.write_text("partial-venv", encoding="utf-8")
        fail("venv")
    elif args[:2] == ["pip", "install"]:
        record("install", source=args[-1])
        state.write_text("partial-install:" + commit, encoding="utf-8")
        fail("install")
        state.write_text("installed:" + commit, encoding="utf-8")
    else:
        sys.exit("unexpected uv command: " + repr(args))
elif name == "python":
    if args[:3] != ["-P", "scripts/gnn_source.py", "check"]:
        sys.exit("unexpected runtime command: " + repr(args))
    record("reader")
    fail("reader")
elif name == "cat":
    record("marker-read")
    print(Path(args[-1]).read_text(encoding="utf-8"), end="")
    fail("marker-read")
elif name == "rm":
    path = Path(args[-1])
    phase = "invalidate" if path == marker else "cleanup"
    record(phase)
    fail(phase)
    path.unlink(missing_ok=True)
elif name == "mkdir":
    record("mkdir")
    fail("mkdir")
    Path(args[-1]).mkdir(parents=True, exist_ok=True)
elif name == "mktemp":
    record("marker-temp")
    fail("marker-temp")
    template = Path(args[-1])
    fd, path = tempfile.mkstemp(prefix=template.name.removesuffix("XXXXXX"), dir=template.parent)
    os.close(fd)
    print(path)
elif name == "mv":
    record("marker-publish")
    fail("marker-publish")
    os.replace(args[-2], args[-1])
elif name == "git":
    sys.exit(1)  # Measurement records this synthetic repository as unavailable.
else:
    sys.exit("unexpected fixture executable: " + name)
'''

# Bash builtins cannot be intercepted through PATH. Fail after writing all marker
# bytes to catch publication of a marker whose write command nevertheless failed.
BASH_ENV = r'''
printf() {
    if [ "${GATE_FIXTURE_FAIL:-}" = marker-write ] && [ "${1:-}" = '%s\n' ]; then
        builtin printf "$@"
        return 41
    fi
    builtin printf "$@"
}
'''


class GateFixture:
    def __init__(self, root: Path):
        self.root = root
        self.tools = root / "tools"
        self.runtime = root / "cache" / "gnn-runtime"
        self.marker = self.runtime / ".pin-commit"
        self.state = self.runtime / "state"
        self.tools.mkdir()
        (root / "scripts").mkdir()
        (root / "specs").mkdir()
        shutil.copy2(ROOT / "run.sh", root / "run.sh")
        shutil.copy2(ROOT / "scripts" / "gate_report.py", root / "scripts" / "gate_report.py")
        self.driver = self.tools / "command.py"
        self.driver.write_text(f"#!{sys.executable}\n" + COMMAND, encoding="utf-8")
        self.driver.chmod(0o755)
        for name in ("host-python", "julia", "uv", "cat", "rm", "mkdir", "mktemp", "mv", "git"):
            (self.tools / name).symlink_to(self.driver)
        for name in ("bash", "dirname"):
            executable = shutil.which(name)
            if executable is None:
                raise RuntimeError(f"fixture requires {name}")
            (self.tools / name).symlink_to(executable)
        (root / "bash-env").write_text(BASH_ENV, encoding="utf-8")
        self.set_pin(COMMIT)

    def set_pin(self, commit):
        self.commit = commit
        (self.root / "specs" / "gnn-pin.json").write_text(
            json.dumps({"repository": "https://example.invalid/gnn", "commit": commit}),
            encoding="utf-8",
        )

    def seed_cache(self, commit):
        (self.runtime / "bin").mkdir(parents=True, exist_ok=True)
        shutil.copy2(self.driver, self.runtime / "bin" / "python")
        self.marker.write_text(commit + "\n", encoding="utf-8")
        self.state.write_text("installed:" + commit, encoding="utf-8")

    def run(self, *arms, **extra):
        ignored = {"BASH_ENV", "ENV", "VIRTUAL_ENV"}
        env = {
            key: value for key, value in os.environ.items()
            if key not in ignored
            and not key.startswith(("ACTINF_", "GNN_", "GATE_FIXTURE_", "PYTHON", "JULIA", "UV_"))
        }
        env.update(
            PATH=str(self.tools),
            PYTHON=str(self.tools / "host-python"),
            PYTHONDONTWRITEBYTECODE="1",
            JULIA_BIN=str(self.tools / "julia"),
            ACTINF_GATE_DIR=str(self.root / "cache"),
            GATE_FIXTURE_ROOT=str(self.root),
            GATE_FIXTURE_COMMIT=self.commit,
            BASH_ENV=str(self.root / "bash-env"),
        )
        env.update(extra)
        return subprocess.run(
            [str(self.tools / "bash"), "run.sh", *arms], cwd=self.root,
            env=env, stdin=subprocess.DEVNULL, capture_output=True, text=True, timeout=30,
        )

    def events(self):
        log = self.root / "commands.jsonl"
        return [json.loads(line) for line in log.read_text(encoding="utf-8").splitlines()] if log.exists() else []

    def phases(self):
        return [event["phase"] for event in self.events()]


class RunGateTests(unittest.TestCase):
    def setUp(self):
        directory = tempfile.TemporaryDirectory(prefix="actinf-run-gate-")
        self.addCleanup(directory.cleanup)
        self.fixture = GateFixture(Path(directory.name))

    def assert_exit(self, result, expected=0):
        self.assertEqual(result.returncode, expected, result.stdout + result.stderr)

    def assert_full_dispatch(self):
        events = [event for event in self.fixture.events() if event["phase"] == "julia-tests"]
        self.assertEqual([event["arm"] for event in events], ["full"])

    def test_full_overrides_inherited_fast(self):
        self.assert_exit(self.fixture.run("full", ACTINF_RXINFER_TEST_ARM="fast"))
        self.assert_full_dispatch()

    def test_all_overrides_inherited_fast(self):
        # The all arm also checks a real, source-matching documentation receipt.
        # Generate it in this fixture without selecting a Julia test arm.
        self.assert_exit(self.fixture.run("measure", "--arms", "lint"))
        self.assert_exit(self.fixture.run("all", ACTINF_RXINFER_TEST_ARM="fast"))
        self.assert_full_dispatch()
        self.assertIn("reader", self.fixture.phases())

    def test_measured_full_overrides_inherited_fast(self):
        self.assert_exit(self.fixture.run("measure", "--arms", "full", ACTINF_RXINFER_TEST_ARM="fast"))
        self.assert_full_dispatch()
        receipt = json.loads((self.fixture.root / "docs/_generated/gate-receipt.json").read_text())
        full = next(arm for arm in receipt["arms"] if arm["arm"] == "full")
        self.assertEqual(full["tests"], {"passed": 2, "deferred": 0, "total": 2})

    def test_failed_pin_admission_cannot_mutate_a_ready_runtime(self):
        self.fixture.seed_cache(COMMIT)
        self.assert_exit(self.fixture.run("gnn", GATE_FIXTURE_FAIL="pin-admission"), FAILURE)
        self.assertEqual(self.fixture.marker.read_text(), COMMIT + "\n")
        self.assertEqual(self.fixture.state.read_text(), "installed:" + COMMIT)
        for phase in ("invalidate", "install", "validator", "reader", "unit-tests"):
            self.assertNotIn(phase, self.fixture.phases())

    def test_prerequisite_failures_preserve_unchanged_cache(self):
        self.fixture.seed_cache(COMMIT)
        for phase in ("pin-repository", "pin-commit", "marker-read"):
            with self.subTest(phase=phase):
                result = self.fixture.run("gnn", GATE_FIXTURE_FAIL=phase)
                self.assert_exit(result, FAILURE)
                self.assertEqual(self.fixture.marker.read_text(), COMMIT + "\n")
                self.assertEqual(self.fixture.state.read_text(), "installed:" + COMMIT)
        self.assertNotIn("invalidate", self.fixture.phases())
        self.assertNotIn("validator", self.fixture.phases())

    def test_local_checkout_provisioning_cannot_reuse_or_mutate_cache(self):
        self.fixture.seed_cache(COMMIT)
        upstream = self.fixture.root / "upstream"
        upstream.mkdir()
        for root in (upstream, self.fixture.root / "absent"):
            with self.subTest(root=root):
                result = self.fixture.run("gnn", GNN_ROOT=str(root))
                self.assert_exit(result, 2)
                self.assertIn("cannot satisfy canonical Git provenance", result.stderr)
                self.assertEqual(self.fixture.marker.read_text(), COMMIT + "\n")
                self.assertEqual(self.fixture.state.read_text(), "installed:" + COMMIT)
        self.assertNotIn("invalidate", self.fixture.phases())
        self.assertNotIn("install", self.fixture.phases())
        self.assertNotIn("validator", self.fixture.phases())

    def test_missing_uv_reports_not_run_without_mutation(self):
        (self.fixture.tools / "uv").unlink()
        self.assert_exit(self.fixture.run("gnn"), 2)
        self.assertFalse(self.fixture.runtime.exists())
        self.assertNotIn("validator", self.fixture.phases())

    def test_failed_marker_invalidation_stops_before_update(self):
        self.fixture.seed_cache(OLD_COMMIT)
        self.assert_exit(self.fixture.run("gnn", GATE_FIXTURE_FAIL="invalidate"), FAILURE)
        self.assertEqual(self.fixture.marker.read_text(), OLD_COMMIT + "\n")
        self.assertEqual(self.fixture.state.read_text(), "installed:" + OLD_COMMIT)
        self.assertNotIn("mkdir", self.fixture.phases())
        self.assertNotIn("install", self.fixture.phases())
        self.assertNotIn("validator", self.fixture.phases())

    def test_failed_provisioning_never_publishes_readiness(self):
        for phase in ("mkdir", "venv", "install", "marker-temp", "marker-write", "marker-publish"):
            with self.subTest(phase=phase), tempfile.TemporaryDirectory(prefix="actinf-run-gate-") as directory:
                fixture = GateFixture(Path(directory))
                fixture.seed_cache(OLD_COMMIT)
                if phase == "venv":
                    (fixture.runtime / "bin" / "python").unlink()
                self.assert_exit(fixture.run("gnn", GATE_FIXTURE_FAIL=phase), FAILURE)
                self.assertFalse(fixture.marker.exists(), phase)
                self.assertNotIn("validator", fixture.phases())
                if phase in ("mkdir", "venv"):
                    self.assertNotIn("install", fixture.phases())
                for event in fixture.events():
                    if event["phase"] in ("mkdir", "venv", "install", "marker-temp", "marker-publish"):
                        self.assertFalse(event["marker"], event)
                if phase in ("marker-write", "marker-publish"):
                    self.assertEqual(list(fixture.runtime.glob(".pin-commit.*")), [])

    def test_failed_update_retry_installs_before_cache_admission(self):
        self.fixture.seed_cache(OLD_COMMIT)
        self.assert_exit(self.fixture.run("gnn", GATE_FIXTURE_FAIL="install"), FAILURE)
        self.assertFalse(self.fixture.marker.exists())
        self.assertEqual(self.fixture.state.read_text(), "partial-install:" + COMMIT)
        self.assert_exit(self.fixture.run("gnn"))
        self.assertEqual(self.fixture.marker.read_text(), COMMIT + "\n")
        self.assertEqual(self.fixture.state.read_text(), "installed:" + COMMIT)
        self.assertEqual(self.fixture.phases().count("install"), 2)
        self.assert_exit(self.fixture.run("gnn", GATE_FIXTURE_FAIL="install"))
        self.assertEqual(self.fixture.phases().count("install"), 2)

    def test_reverting_pin_cannot_revive_failed_updates_old_marker(self):
        self.fixture.seed_cache(OLD_COMMIT)
        self.assert_exit(self.fixture.run("gnn", GATE_FIXTURE_FAIL="install"), FAILURE)
        self.fixture.set_pin(OLD_COMMIT)
        self.assert_exit(self.fixture.run("gnn", GATE_FIXTURE_FAIL="install"), FAILURE)
        self.assertFalse(self.fixture.marker.exists())
        self.assertEqual(self.fixture.phases().count("install"), 2)
        self.assertNotIn("validator", self.fixture.phases())

    def test_matching_cache_is_reused_without_mutation(self):
        self.fixture.seed_cache(COMMIT)
        self.assert_exit(self.fixture.run("gnn", GATE_FIXTURE_FAIL="invalidate"))
        self.assertEqual(self.fixture.marker.read_text(), COMMIT + "\n")
        self.assertEqual(self.fixture.state.read_text(), "installed:" + COMMIT)
        for phase in ("invalidate", "mkdir", "venv", "install", "marker-temp", "marker-publish"):
            self.assertNotIn(phase, self.fixture.phases())
        self.assertIn("reader", self.fixture.phases())

    def test_failed_validator_never_reaches_shared_checker(self):
        self.fixture.seed_cache(COMMIT)
        self.assert_exit(self.fixture.run("gnn", GATE_FIXTURE_FAIL="validator"), FAILURE)
        self.assertIn("validator", self.fixture.phases())
        self.assertNotIn("reader", self.fixture.phases())
        self.assertNotIn("unit-tests", self.fixture.phases())

    def test_failed_shared_checker_never_reaches_unit_tests(self):
        self.fixture.seed_cache(COMMIT)
        self.assert_exit(self.fixture.run("gnn", GATE_FIXTURE_FAIL="reader"), FAILURE)
        self.assertIn("reader", self.fixture.phases())
        self.assertNotIn("unit-tests", self.fixture.phases())

    def test_explicit_source_mode_does_not_provision_an_implicit_runtime(self):
        self.assert_exit(self.fixture.run("gnn", GNN_ORIGIN_MODE="source"), 2)
        self.assertFalse(self.fixture.runtime.exists())
        self.assertNotIn("install", self.fixture.phases())
        self.assertNotIn("validator", self.fixture.phases())


if __name__ == "__main__":
    unittest.main()
