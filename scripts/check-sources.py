#!/usr/bin/env python3
"""Self-check: validate sources.yaml and the local skill paths it lists.

Run with: python scripts/check-sources.py
Exits 0 if everything matches, 1 otherwise. Intentionally small — no
fixtures, no cloning, no network. Catches: manifest typos, missing local
paths, mismatched upstream_path mappings, schema drift.
"""
from __future__ import annotations

import re
import sys
from pathlib import Path

import yaml

REPO_ROOT = Path(__file__).resolve().parent.parent
MANIFEST = REPO_ROOT / "sources.yaml"


def main() -> int:
    if not MANIFEST.exists():
        print(f"FAIL: {MANIFEST} not found")
        return 1
    data = yaml.safe_load(MANIFEST.read_text())
    sources = data.get("sources")
    if not isinstance(sources, list):
        print("FAIL: top-level `sources:` must be a list")
        return 1

    errors: list[str] = []
    seen_paths: set[str] = set()

    for i, entry in enumerate(sources):
        loc = f"sources[{i}]"
        if not isinstance(entry, dict):
            errors.append(f"{loc}: entry must be a mapping")
            continue
        if "path" not in entry:
            errors.append(f"{loc}: missing `path`")
            continue
        path = entry["path"]
        if path in seen_paths:
            errors.append(f"{loc}: duplicate path {path!r}")
        seen_paths.add(path)

        local = bool(entry.get("local", False))
        if local:
            # Local entries need no upstream, but the path should exist.
            if not (REPO_ROOT / path).exists():
                errors.append(f"{loc}: local entry path {path!r} does not exist")
            continue

        if "repo" not in entry:
            errors.append(f"{loc}: non-local entry missing `repo`")
            continue
        repo = entry["repo"]
        if not re.match(r"^https://[\w./-]+$", repo):
            errors.append(f"{loc}: invalid repo URL {repo!r}")

        # Local skill dir must exist (we're syncing INTO it).
        if not (REPO_ROOT / path).exists():
            errors.append(f"{loc}: target path {path!r} does not exist locally")

        # Sanity-check upstream_path (relative, no leading slash, no parent traversal).
        upstream = entry.get("upstream_path", path)
        if upstream.startswith("/") or ".." in upstream.split("/"):
            errors.append(f"{loc}: suspicious upstream_path {upstream!r}")

    if errors:
        print(f"FAIL: {len(errors)} error(s) in sources.yaml:")
        for e in errors:
            print(f"  - {e}")
        return 1

    print(f"OK: {len(sources)} sources validated "
          f"({sum(1 for s in sources if not s.get('local'))} upstream, "
          f"{sum(1 for s in sources if s.get('local'))} local)")
    return 0


if __name__ == "__main__":
    sys.exit(main())
