"""Lint arm: syntax checks for every tracked file, with no third-party imports.

This is the `lint` arm of `./run.sh`. It checks the working tree, not a commit:
tracked files plus untracked files that `.gitignore` does not exclude, so a new
file is linted before it is staged. Nothing is formatted or rewritten.

Checks:

* ``.jl`` — every expression parses; a file with a ``:incomplete`` or ``:error``
  node fails (Julia reports both without raising, so the nodes are walked).
* ``.py`` — every file compiles under ``ast.parse``.
* ``.json`` — every file is valid JSON.
* ``.sh`` — every file passes ``bash -n`` and has the executable bit set
  (skipped, with a notice, when ``bash`` is not installed).

There is no type-check arm: the package is Julia, the repository declares no
static type checker, and ``test/runtests.jl`` is the only checked contract.

Usage: ``python3 scripts/lint.py [--julia JULIA] [--json]``

Exit codes: ``0`` clean, ``1`` findings, ``2`` a required tool is unavailable.
"""

from __future__ import annotations

import argparse
import ast
import json
import os
import shutil
import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]

JULIA_PARSE_PROGRAM = r"""
summary(err) = begin
    story = split(sprint(showerror, err), '\n')
    located = findfirst(line -> occursin("# Error @", line), story)
    located === nothing ? strip(first(story)) : strip(story[located])
end
failures = String[]
for path in ARGS
    node = try
        Meta.parseall(read(path, String))
    catch err
        push!(failures, string(path, ": could not be read: ", summary(err)))
        continue
    end
    stack = Any[node]
    while !isempty(stack)
        ex = pop!(stack)
        ex isa Expr || continue
        if ex.head === :incomplete || ex.head === :error
            push!(failures, string(path, ": ", summary(ex.args[1])))
        else
            append!(stack, ex.args)
        end
    end
end
for failure in failures
    println(failure)
end
isempty(failures) || exit(1)
"""


def working_tree_files() -> list[str]:
    """Return tracked files plus untracked files that are not ignored."""
    try:
        payload = subprocess.run(
            ["git", "ls-files", "-z", "--cached", "--others", "--exclude-standard"],
            cwd=ROOT,
            check=True,
            capture_output=True,
        ).stdout
    except FileNotFoundError:
        raise SystemExit("lint: git is required to enumerate files")
    except subprocess.CalledProcessError as exc:
        raise SystemExit(f"lint: git ls-files failed: {exc.stderr.decode()}")
    return sorted({name for name in payload.decode().split("\0") if name})


def check_julia(paths: list[str], julia: str) -> list[str]:
    if not paths:
        return []
    try:
        completed = subprocess.run(
            [julia, "--startup-file=no", "--compile=min", "-e", JULIA_PARSE_PROGRAM, *paths],
            cwd=ROOT,
            capture_output=True,
            text=True,
        )
    except FileNotFoundError:
        raise SystemExit(f"lint: julia interpreter {julia!r} was not found")
    if completed.returncode == 0:
        return []
    findings = [line for line in completed.stdout.splitlines() if line.strip()]
    if not findings:
        findings = [f"julia parser exited {completed.returncode}: {completed.stderr.strip()}"]
    return findings


def check_python(path: Path) -> list[str]:
    try:
        ast.parse(path.read_text(encoding="utf-8"), filename=str(path))
    except (SyntaxError, UnicodeDecodeError) as exc:
        return [f"{path.relative_to(ROOT)}: {exc}"]
    return []


def check_json(path: Path) -> list[str]:
    try:
        json.loads(path.read_text(encoding="utf-8"))
    except (json.JSONDecodeError, UnicodeDecodeError) as exc:
        return [f"{path.relative_to(ROOT)}: {exc}"]
    return []


def check_shell(path: Path, bash: str) -> list[str]:
    findings: list[str] = []
    completed = subprocess.run(
        [bash, "-n", str(path)], cwd=ROOT, capture_output=True, text=True
    )
    if completed.returncode != 0:
        detail = (completed.stderr or completed.stdout).strip().splitlines()
        findings.append(
            f"{path.relative_to(ROOT)}: {detail[0] if detail else 'bash -n failed'}"
        )
    if not os.access(path, os.X_OK):
        findings.append(f"{path.relative_to(ROOT)}: not executable (chmod +x)")
    return findings


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--julia", default=os.environ.get("JULIA_BIN", "julia"))
    parser.add_argument("--json", action="store_true", help="print a JSON report")
    args = parser.parse_args(argv)

    files = working_tree_files()
    by_suffix: dict[str, list[str]] = {}
    for name in files:
        suffix = Path(name).suffix
        if suffix in {".jl", ".py", ".json", ".sh"}:
            by_suffix.setdefault(suffix, []).append(name)

    findings: list[str] = []
    bash = shutil.which("bash")
    if bash is None:
        print("lint: bash not found; skipping shell syntax checks", file=sys.stderr)

    findings += check_julia(by_suffix.get(".jl", []), args.julia)
    for name in by_suffix.get(".py", []):
        findings += check_python(ROOT / name)
    for name in by_suffix.get(".json", []):
        findings += check_json(ROOT / name)
    if bash is not None:
        for name in by_suffix.get(".sh", []):
            findings += check_shell(ROOT / name, bash)

    counts = {suffix.lstrip("."): len(names) for suffix, names in sorted(by_suffix.items())}
    if args.json:
        print(json.dumps({"ok": not findings, "checked": counts, "findings": findings}))
    else:
        print("lint: checked " + ", ".join(f"{n} {s}" for s, n in counts.items()))
        for finding in findings:
            print(f"lint: {finding}", file=sys.stderr)
        print("lint: clean" if not findings else f"lint: {len(findings)} finding(s)")
    return 1 if findings else 0


if __name__ == "__main__":
    raise SystemExit(main())
