"""Docs arm: check relative Markdown links, anchors, and the docs index.

This is the ``docs`` arm of ``./run.sh``. It reads every Markdown file in the
working tree (tracked plus untracked-but-not-ignored) and reports:

* a relative link whose target path does not exist;
* a ``#fragment`` whose heading or explicit anchor is absent from the target;
* an absolute filesystem link (``/path``), which cannot resolve in a checkout;
* a documentation page that the hub ``docs/index.md`` does not link;
* a long-lived documentation page that ``docs/documentation-index.md`` does not
  list.

External links are not fetched: the check is offline by design, so an
unreachable URL is a separate, manual review step. If the repository ever
adopts ``mkdocs`` or ``markdown-link-check``, fold this arm into that command
instead of keeping both.

Usage: ``python3 scripts/check_links.py [--json]``

Exit codes: ``0`` clean, ``1`` findings, ``2`` the repository layout is missing
an expected file.
"""

from __future__ import annotations

import argparse
import json
import re
import subprocess
import sys
import urllib.parse
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
DOCS = ROOT / "docs"
HUB = DOCS / "index.md"
INDEX = DOCS / "documentation-index.md"

INLINE_LINK = re.compile(r"!?\[[^\]]*\]\(\s*(<[^>]*>|[^)\s]+)(?:\s+[\"'][^\"']*[\"'])?\s*\)")
REFERENCE_DEFINITION = re.compile(r"^\s{0,3}\[[^\]]+\]:\s*(\S+)")
INLINE_CODE = re.compile(r"`[^`]*`")
EXPLICIT_ANCHOR = re.compile(r"<a\s+(?:id|name)=[\"']([^\"']+)[\"']", re.IGNORECASE)
ATTRIBUTE_ANCHOR = re.compile(r"\{#([^}]+)\}\s*$")
ATX_HEADING = re.compile(r"^\s{0,3}(#{1,6})\s+(.*?)\s*#*\s*$")
FENCE = re.compile(r"^\s{0,3}(```|~~~)")


def working_tree_files() -> list[str]:
    payload = subprocess.run(
        ["git", "ls-files", "-z", "--cached", "--others", "--exclude-standard"],
        cwd=ROOT,
        check=True,
        capture_output=True,
    ).stdout
    return sorted({name for name in payload.decode().split("\0") if name})


def slugify(heading: str) -> str:
    """Approximate the GitHub anchor for a heading."""
    text = re.sub(r"`([^`]*)`", r"\1", heading)
    text = re.sub(r"!?\[([^\]]*)\]\([^)]*\)", r"\1", text)
    text = re.sub(r"[*~]", "", text)
    text = text.strip().lower()
    text = re.sub(r"[^\w\- ]", "", text)
    return text.replace(" ", "-")


def anchors(path: Path) -> set[str]:
    """Return every heading slug and explicit anchor id in a Markdown file."""
    found: set[str] = set()
    seen: dict[str, int] = {}
    in_fence = False
    for line in path.read_text(encoding="utf-8").splitlines():
        if FENCE.match(line):
            in_fence = not in_fence
            continue
        if in_fence:
            continue
        for explicit in EXPLICIT_ANCHOR.findall(line):
            found.add(explicit)
        heading = ATX_HEADING.match(line)
        if heading:
            text = heading.group(2)
            attribute = ATTRIBUTE_ANCHOR.search(text)
            if attribute:
                found.add(attribute.group(1))
                continue
            slug = slugify(text)
            count = seen.get(slug, 0)
            seen[slug] = count + 1
            found.add(slug if count == 0 else f"{slug}-{count}")
    return found


def link_targets(path: Path) -> list[tuple[int, str]]:
    """Return ``(line number, raw target)`` for every link in a Markdown file."""
    targets: list[tuple[int, str]] = []
    in_fence = False
    for number, line in enumerate(path.read_text(encoding="utf-8").splitlines(), start=1):
        if FENCE.match(line):
            in_fence = not in_fence
            continue
        if in_fence:
            continue
        stripped = INLINE_CODE.sub("", line)
        for raw in INLINE_LINK.findall(stripped):
            targets.append((number, raw))
        definition = REFERENCE_DEFINITION.match(line)
        if definition:
            targets.append((number, definition.group(1)))
    return targets


def is_external(target: str) -> bool:
    return (
        "://" in target
        or target.startswith(("mailto:", "doi:", "www.", "//"))
    )


def check_file(path: Path, anchor_cache: dict[Path, set[str]]) -> list[str]:
    findings: list[str] = []
    relative = path.relative_to(ROOT)
    for number, raw in link_targets(path):
        target = raw[1:-1] if raw.startswith("<") and raw.endswith(">") else raw
        target = target.strip()
        if not target or is_external(target):
            continue
        location = f"{relative}:{number}"
        if target.startswith("#"):
            fragment = target[1:]
            if fragment and fragment not in anchor_cache.setdefault(path, anchors(path)):
                findings.append(f"{location}: missing anchor #{fragment} in {relative}")
            continue
        if target.startswith("/"):
            findings.append(f"{location}: absolute link {target} cannot resolve in a checkout")
            continue
        path_part, _, fragment = target.partition("#")
        path_part = urllib.parse.unquote(path_part)
        resolved = (path.parent / path_part).resolve()
        if not resolved.exists():
            findings.append(f"{location}: missing link target {target}")
            continue
        if fragment and resolved.is_file() and resolved.suffix == ".md":
            if fragment not in anchor_cache.setdefault(resolved, anchors(resolved)):
                findings.append(
                    f"{location}: missing anchor #{fragment} in "
                    f"{resolved.relative_to(ROOT)}"
                )
    return findings


def linked_targets(hub: Path) -> set[Path]:
    resolved: set[Path] = set()
    for _, raw in link_targets(hub):
        target = raw[1:-1] if raw.startswith("<") and raw.endswith(">") else raw
        path_part, _, _ = urllib.parse.unquote(target).partition("#")
        if not path_part or is_external(path_part) or path_part.startswith("/"):
            continue
        resolved.add((hub.parent / path_part).resolve())
    return resolved


def check_hub(anchor_cache: dict[Path, set[str]]) -> list[str]:
    findings: list[str] = []
    for required in (HUB, INDEX):
        if not required.exists():
            findings.append(f"{required.relative_to(ROOT)}: required documentation file is missing")
    if findings:
        return findings

    hub_targets = linked_targets(HUB)
    for page in sorted(DOCS.rglob("*.md")):
        if page.name in {"README.md", "AGENTS.md"} or page.resolve() == HUB.resolve():
            continue
        if page.resolve() not in hub_targets:
            findings.append(
                f"docs/{page.relative_to(DOCS)}: not linked from docs/index.md"
            )

    index_targets = linked_targets(INDEX)
    for page in sorted(DOCS.glob("*.md")):
        if page.name in {"README.md", "AGENTS.md"} or page.resolve() in {
            HUB.resolve(),
            INDEX.resolve(),
        }:
            continue
        if page.resolve() not in index_targets:
            findings.append(
                f"docs/{page.relative_to(DOCS)}: not listed in docs/documentation-index.md"
            )
    return findings


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--json", action="store_true", help="print a JSON report")
    args = parser.parse_args(argv)

    markdown = [name for name in working_tree_files() if name.endswith(".md")]
    anchor_cache: dict[Path, set[str]] = {}
    findings: list[str] = []
    for name in markdown:
        findings += check_file(ROOT / name, anchor_cache)
    findings += check_hub(anchor_cache)

    if args.json:
        print(json.dumps({"ok": not findings, "files": len(markdown), "findings": findings}))
    else:
        print(f"docs: checked {len(markdown)} markdown files")
        for finding in findings:
            print(f"docs: {finding}", file=sys.stderr)
        print("docs: clean" if not findings else f"docs: {len(findings)} finding(s)")
    return 1 if findings else 0


if __name__ == "__main__":
    raise SystemExit(main())
