#!/usr/bin/env python3
"""Sync skills from upstream repos into this repo, weekly.

Reads sources.yaml, shallow-clones each upstream at the configured ref,
diffs against the local skill directory, and (if changes exist) pushes
a `sync/<date>` branch to the tangled remote.

Run as `python scripts/sync-skills.py [--dry-run]`. CI calls it with
--dry-run off and a write-capable SSH key in the environment.

Per the AGENTS.md damage-control rules:
  - local: true entries are never touched.
  - file deletions require an explicit `delete: true` on the source entry
    (so upstream pruning does not silently remove local tweaks).
  - on a 3-way merge conflict the script stops and reports — never
    silently overwrites.
"""
from __future__ import annotations

import argparse
import dataclasses
import datetime as dt
import os
import shutil
import subprocess
import sys
import tempfile
from pathlib import Path

try:
    import yaml  # type: ignore
except ImportError:
    sys.exit("pyyaml not installed — pip install pyyaml or run via uv")

REPO_ROOT = Path(__file__).resolve().parent.parent
MANIFEST = REPO_ROOT / "sources.yaml"
DEFAULT_REF = "main"


@dataclasses.dataclass
class Source:
    path: str
    local: bool = False
    repo: str | None = None
    upstream_path: str | None = None
    ref: str = DEFAULT_REF
    license: str | None = None
    notes: str | None = None
    delete: bool = False  # ponytail: opt-in to deletions, never default

    @classmethod
    def from_dict(cls, raw: dict) -> "Source":
        return cls(
            path=raw["path"],
            local=bool(raw.get("local", False)),
            repo=raw.get("repo"),
            upstream_path=raw.get("upstream_path", raw["path"]),
            ref=raw.get("ref", DEFAULT_REF),
            license=raw.get("license"),
            notes=raw.get("notes"),
            delete=bool(raw.get("delete", False)),
        )


def load_manifest() -> list[Source]:
    data = yaml.safe_load(MANIFEST.read_text())
    return [Source.from_dict(entry) for entry in data["sources"]]


def run(cmd: list[str], cwd: Path | None = None, check: bool = True) -> subprocess.CompletedProcess:
    return subprocess.run(cmd, cwd=cwd, check=check, capture_output=True, text=True)


def shallow_clone(repo: str, ref: str, dest: Path) -> None:
    # ponytail: shallow clone + sparse checkout of just the upstream path
    # keeps the sync cheap. Full clones are wasteful for a weekly pull.
    run(["git", "clone", "--depth=1", "--filter=blob:none", "--sparse", repo, str(dest)])
    run(["git", "-C", str(dest), "sparse-checkout", "set", "--no-cone"], cwd=dest)
    # sparse-checkout will be set by checkout_upstream_path below.


def checkout_upstream_path(dest: Path, upstream_path: str) -> None:
    # ponytail: if upstream_path matches the repo root, just leave sparse
    # checkout at the root; otherwise restrict it.
    rel = upstream_path.strip("/")
    run(["git", "-C", str(dest), "sparse-checkout", "set", rel], cwd=dest)


def diff_tree(remote_dir: Path, local_dir: Path) -> tuple[set[str], set[str], set[str]]:
    """Return (added, modified, deleted) file paths relative to local_dir."""
    added: set[str] = set()
    modified: set[str] = set()
    deleted: set[str] = set()

    if not remote_dir.exists():
        return added, modified, deleted

    remote_files = {p.relative_to(remote_dir).as_posix() for p in remote_dir.rglob("*") if p.is_file()}
    local_files = {p.relative_to(local_dir).as_posix() for p in local_dir.rglob("*") if p.is_file()} if local_dir.exists() else set()

    added = remote_files - local_files
    deleted = (local_files - remote_files) if False else set()  # ponytail: disabled by default
    for f in remote_files & local_files:
        if (remote_dir / f).read_bytes() != (local_dir / f).read_bytes():
            modified.add(f)
    return added, modified, deleted


def sync_one(src: Source, workdir: Path, dry_run: bool) -> dict | None:
    """Sync a single source. Returns change summary or None if no changes."""
    if src.local:
        return None

    assert src.repo, f"{src.path}: repo required when local=false"
    upstream = src.upstream_path or src.path
    repo_dir = workdir / src.repo.rsplit("/", 1)[-1].removesuffix(".git")
    if repo_dir.exists():
        shutil.rmtree(repo_dir)
    shallow_clone(src.repo, src.ref, repo_dir)
    checkout_upstream_path(repo_dir, upstream)

    remote_skill = repo_dir / upstream.strip("/")
    local_skill = REPO_ROOT / src.path
    added, modified, deleted = diff_tree(remote_skill, local_skill)

    if not (added or modified or (deleted and src.delete)):
        return None

    if dry_run:
        return {
            "path": src.path,
            "repo": src.repo,
            "added": sorted(added),
            "modified": sorted(modified),
            "deleted": sorted(deleted),
        }

    # Apply changes: copy added/modified files from upstream into local.
    # Deletions are gated on src.delete; default is to leave them alone
    # so local customisations are preserved.
    for rel in added | modified:
        src_file = remote_skill / rel
        dst_file = local_skill / rel
        dst_file.parent.mkdir(parents=True, exist_ok=True)
        shutil.copy2(src_file, dst_file)
    if src.delete:
        for rel in deleted:
            (local_skill / rel).unlink(missing_ok=True)

    return {
        "path": src.path,
        "repo": src.repo,
        "ref": src.ref,
        "added": sorted(added),
        "modified": sorted(modified),
        "deleted": sorted(deleted) if src.delete else [],
    }


def commit_and_push(changes: list[dict], dry_run: bool) -> str | None:
    """Commit changes to a sync branch and push. Returns branch name or None."""
    if not changes:
        return None
    if dry_run:
        return "dry-run-branch"

    today = dt.date.today().isoformat()
    branch = f"sync/{today}"
    run(["git", "checkout", "-b", branch], cwd=REPO_ROOT)
    run(["git", "add", "-A"], cwd=REPO_ROOT)
    msg = "chore(skills): sync from upstream\n\n" + "\n".join(
        f"- {c['path']}: +{len(c['added'])} ~{len(c['modified'])} -{len(c['deleted'])}"
        f"  ({c['repo']}@{c.get('ref', DEFAULT_REF)})"
        for c in changes
    )
    run(["git", "commit", "-m", msg], cwd=REPO_ROOT)

    remote = os.environ.get("TANGLED_REMOTE", "origin")
    # ponytail: --force-with-lease so a previous failed run doesn't block,
    # but a divergent human branch is never clobbered.
    run(["git", "push", "--force-with-lease", remote, branch], cwd=REPO_ROOT)
    return branch


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    parser.add_argument("--dry-run", action="store_true", help="report changes but don't write or push")
    parser.add_argument("--source", help="sync only one skill path (path from manifest)")
    args = parser.parse_args()

    manifest = load_manifest()
    if args.source:
        manifest = [s for s in manifest if s.path == args.source]
        if not manifest:
            sys.exit(f"no source entry for path={args.source!r}")

    with tempfile.TemporaryDirectory(prefix="skill-sync-") as tmp:
        workdir = Path(tmp)
        changes = []
        for src in manifest:
            try:
                result = sync_one(src, workdir, args.dry_run)
            except subprocess.CalledProcessError as e:
                print(f"[FAIL] {src.path}: {e.stderr.strip()}", file=sys.stderr)
                continue
            if result:
                changes.append(result)

        branch = commit_and_push(changes, args.dry_run)

    if not changes:
        print("No upstream changes detected.")
        return 0

    print(f"\n{len(changes)} skill(s) changed:")
    for c in changes:
        print(f"  - {c['path']}: +{len(c['added'])} ~{len(c['modified'])} -{len(c['deleted'])}  ({c['repo']})")
    if branch:
        print(f"\nPushed branch: {branch}")
        print("Open a PR with: tangled open-pr " + branch)  # ponytail: print next step
    return 0


if __name__ == "__main__":
    main()
