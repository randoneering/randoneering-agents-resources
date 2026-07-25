# Randoneering Agent Resources

Skills, agents, and pi-flavored agent overrides for OpenCode, pi, and Claude Code.

Two parallel agent sets: portable prompts under `agents/` (frontmatter subset `name` + `description`) and pi-specific overrides under `pi-agent/agents/` (extended frontmatter, harness-targeted). Skill format stays the same across both harnesses.

## Skills

| Category | Skills |
|----------|--------|
| **Core Workflow** | [using-superpowers](skills/using-superpowers/), [brainstorming](skills/brainstorming/), [writing-plans](skills/writing-plans/), [executing-plans](skills/executing-plans/) |
| **Development Workflow** | [test-driven-development](skills/test-driven-development/), [subagent-driven-development](skills/subagent-driven-development/), [dispatching-parallel-agents](skills/dispatching-parallel-agents/), [using-git-worktrees](skills/using-git-worktrees/), [finishing-a-development-branch](skills/finishing-a-development-branch/) |
| **Quality** | [systematic-debugging](skills/systematic-debugging/), [damage-control](skills/damage-control/), [verification-before-completion](skills/verification-before-completion/) |
| **Code Review** | [requesting-code-review](skills/requesting-code-review/), [receiving-code-review](skills/receiving-code-review/) |
| **Writing** | [documentation-writing](skills/documentation-writing/), [writing-skills](skills/writing-skills/), [writing-style](skills/writing-style/), [resume-tailor](skills/resume-tailor/) |
| **Compression (caveman family)** | [caveman](skills/caveman/) (mode), [cavecrew](skills/cavecrew/) (delegation guide), [caveman-commit](skills/caveman-commit/), [caveman-compress](skills/caveman-compress/), [caveman-help](skills/caveman-help/), [caveman-review](skills/caveman-review/), [caveman-stats](skills/caveman-stats/) |
| **Data** | [dbt](skills/dbt/), [postgres](skills/postgres/), [snowflake](skills/snowflake/), [clickhouse](skills/clickhouse/), [neon](skills/neon/) |
| **Stacks** | [python](skills/python/), [nix](skills/nix/), [automation](skills/automation/), [flox](skills/flox/) |
| **Cloud & Infrastructure** | [cloudflare](skills/cloudflare/), [hashicorp](skills/hashicorp/) |
| **Security** | [trail_of_bits](skills/trail_of_bits/), [sentry](skills/sentry/) |

Caveman family reduces token use while keeping full technical accuracy. `caveman` is the mode; `cavecrew` routes subagent output through compressed presenters; the rest are command-shaped skills (commit messages, code review, memory-file compression, help card, session stats).

## Agents — Portable (`agents/`)

Generic prompts with portable frontmatter (`name`, `description`).

| Category | Contents |
|----------|----------|
| **Engineering** | [agents/engineering](agents/engineering/) — implementation, architecture, security, DevOps, review |
| **Marketing** | [agents/marketing](agents/marketing/) — content, campaign, paid media, SEO, growth |
| **Product** | [agents/product](agents/product/) — research, prioritization, feedback synthesis |
| **Project Management** | [agents/project-management](agents/project-management/) — planning, tracking, workflow |
| **Specialized** | [agents/specialized](agents/specialized/) — sales, finance, legal, domain specialists |
| **Support** | [agents/support](agents/support/) — reporting, compliance, infrastructure, finance |
| **Testing** | [agents/testing](agents/testing/) — evidence, API, accessibility, performance |

## Agents — pi (`pi-agent/agents/`)

Same filenames, pi-harness overrides (extended frontmatter, tool routing, prompt tweaks that depend on pi features). Use when running inside pi.

| Category | Contents |
|----------|----------|
| **Engineering** | [pi-agent/agents/engineering](pi-agent/agents/engineering/) |
| **Marketing** | [pi-agent/agents/marketing](pi-agent/agents/marketing/) |
| **Product** | [pi-agent/agents/product](pi-agent/agents/product/) |
| **Project Management** | [pi-agent/agents/project-management](pi-agent/agents/project-management/) |
| **Specialized** | [pi-agent/agents/specialized](pi-agent/agents/specialized/) |
| **Support** | [pi-agent/agents/support](pi-agent/agents/support/) |
| **Testing** | [pi-agent/agents/testing](pi-agent/agents/testing/) |

## Claude Code Bundle (`.claude/`)

Drop-in assets for Claude Code. The `skills/` mirror under `.claude/skills/` is a curated subset of the canonical `skills/` tree.

| Path | Contents |
|------|----------|
| `.claude/CLAUDE.md` | Project instructions for Claude Code |
| `.claude/commands/` | [acceptance-criteria](.claude/commands/acceptance-criteria.md), [analyze-permissions](.claude/commands/analyze-permissions.md), [analyze-skills](.claude/commands/analyze-skills.md), [commit](.claude/commands/commit.md), [install](.claude/commands/install.md), [optimize-prompt](.claude/commands/optimize-prompt.md), [optimize-ruleset](.claude/commands/optimize-ruleset.md), [optimize-skill](.claude/commands/optimize-skill.md), [prime](.claude/commands/prime.md), [prompt-help](.claude/commands/prompt-help.md), [sentient](.claude/commands/sentient.md) |
| `.claude/skills/` | Curated subset of [skills/](skills/) — 23 skills covering core workflow, writing, data, and stacks |
| `.claude/templates/` | [cli-tools](.claude/templates/cli-tools.md), [data-engineering](.claude/templates/data-engineering.md), [nix-packaging](.claude/templates/nix-packaging.md), [python-api](.claude/templates/python-api.md) |

## Structure

```
agents/                  # portable agent prompts (name + description frontmatter)
├── {category}/
│   └── <domain>-<role>.md
│
pi-agent/                # pi-harness agent overrides
└── agents/
    └── {category}/
        └── <domain>-<role>.md
│
skills/                  # SKILL.md-format skills (Agent Skills spec)
└── {category}/
    └── {skill}/
        ├── SKILL.md
        ├── references/  # optional
        └── scripts/     # optional (e.g. caveman-compress)
│
.claude/                 # Claude Code drop-in bundle
├── CLAUDE.md
├── commands/            # slash commands
├── skills/              # skill subset
└── templates/           # starter templates
```

## Usage

- **OpenCode**: copy skills into `.claude/skills/` or reference this repo via `AGENTS.md`
- **pi**: copy skills into `.pi/skills/` or `.agents/skills/`, or point pi at this repo via its `skills` setting; use `pi-agent/agents/` for pi-tuned prompts
- **Claude Code**: the `.claude/` directory is a drop-in bundle — copy or symlink the whole tree, or pick `commands/` / `skills/` / `templates/` individually
- **Portable agents**: files in `agents/` work as prompt templates, imported agents, or source material for tool-specific packaging

## Configuration

- OpenCode reads `AGENTS.md`
- pi reads `AGENTS.md` and supports `CLAUDE.md`
- Claude Code reads `CLAUDE.md` (this repo's lives at `.claude/CLAUDE.md`)
- Use repo-local `AGENTS.md` for cross-harness shared instructions

## Compatibility

- Skills use the Agent Skills `SKILL.md` structure — all three harnesses consume them
- Skills may include optional frontmatter (`allowed-tools`, `compatibility`, `metadata`, `user-invocable`); unknown fields are ignored
- Portable agents keep only `name` + `description`; pi overrides extend with harness-specific frontmatter
- Runtime features still vary by harness. Skills that mention subagents, todo tools, or platform-specific commands may require harness-specific adaptation

## License

GPLv3 — see [LICENSE](LICENSE)