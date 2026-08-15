# Weekly skill sync CI

This repo syncs its skills from upstream sources once a week.

## Architecture

```
┌──────────────────────────┐        ┌────────────────────────────┐
│ GitHub Actions cron      │        │ Tangled CI                 │
│ (.github/workflows/      │  push  │ (.tangled/workflows/       │
│  weekly-sync.yaml)       │ ─────► │  sync-skills.yaml)         │
│                          │        │                            │
│  weekly cron fires       │        │  shallow-clones upstreams  │
│  empty commit to         │        │  from sources.yaml,        │
│  sync-scheduler branch   │        │  pushes sync/<date> branch │
└──────────────────────────┘        └────────────────────────────�
```

Tangled CI has no native cron trigger, so GitHub Actions drives it. The sync logic itself runs in Tangled.

## Setup (one-time)

### 1. Mirror this tangled repo to GitHub

Mirror `git@tangled.org:did:plc:.../randoneering-agents-resources.git` to a GitHub repo (e.g. `your-org/randoneering-agents-resources`). Tangled's "Mirroring a repository to Tangled" doc covers the reverse; the forward direction is a regular `git remote add` + push.

### 2. Configure secrets

**Tangled side** (repo settings at tangled.app):
- `TANGLED_SSH_KEY` — SSH key with write access to the tangled repo. Used by `.tangled/workflows/sync-skills.yaml` to push the `sync/<date>` branch.

**GitHub side** (the mirror repo's settings):
- Secret `TANGLED_SSH_KEY` — same key.
- Variable `TANGLED_REPO_SSH_URL` — the SSH URL of the tangled repo, e.g. `git@tangled.org:did:plc:xxxxxxxx/repo.git`.

### 3. Make sure the SSH key is trusted

The key must be in the repo owner's `~/.ssh/authorized_keys` on the knot hosting the tangled repo.

### 4. Test

Trigger the GitHub Actions workflow manually (`workflow_dispatch` is exposed) and watch the tangled CI run appear at tangled.app.

## What the sync does

1. Reads `sources.yaml` (33 upstream entries, 21 local).
2. For each upstream skill, shallow-clones the source repo and diffs against the local copy.
3. If anything changed, pushes a `sync/<date>` branch with the additions/modifications and opens a PR.

`local: true` skills are never touched. File deletions require `delete: true` on the manifest entry (off by default so upstream pruning never silently removes local tweaks).

## Schedule

Weekly: Sunday 06:00 UTC. Change in `.github/workflows/weekly-sync.yaml`.

## Alternatives if you don't want a GitHub mirror

Point any free cron service (cron-job.org, EasyCron, etc.) at the workflow's manual-trigger URL on tangled.app. The workflow's `event: ["manual"]` trigger supports this. The GitHub Actions file is then unused.
