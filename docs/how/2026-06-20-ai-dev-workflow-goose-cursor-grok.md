# AI development workflow: Goose, Cursor, and Grok

Overview of how to combine **Goose**, **Cursor**, and **Grok** for software development on macOS — based on research from June 2026. This is a practical stack guide, not an official integration from any vendor.

---

## Summary

There is no single “Goose + Cursor + Grok” product. The pattern that works best is:

1. **One shared project brain** — `AGENTS.md` plus tool-specific rules
2. **Cursor** — interactive IDE work, planning, and in-editor agent edits
3. **Grok Build** — terminal-first automation, parallel subagents, scripted runs
4. **Goose** — orchestration, MCP integrations, repeatable recipes, remote sessions

You already have the **Goose desktop app** (including remote use). That covers a large part of the stack. The main additions are **Cursor** and optionally **Grok Build CLI**.

---

## What each tool is best at

| Tool | Role | Best for |
|------|------|----------|
| **Cursor** | AI-native IDE | Day-to-day coding, `@file` context, Plan Mode, multi-file Agent/Composer |
| **Goose** | Open-source agent (CLI + desktop + API) | Autonomous tasks, MCP (GitHub, Slack, DB, …), recipes, provider switching, remote sessions |
| **Grok / Grok Build** | xAI terminal coding agent | Plan → approve → execute in CLI, parallel worktrees, headless automation |

### Division of labor (typical feature flow)

| Phase | Tool |
|-------|------|
| Explore codebase | Cursor (Ask + `@codebase`) |
| Plan a feature | Cursor Plan Mode **or** Grok plan mode |
| Implement interactively | Cursor Agent / Composer |
| Batch refactors / parallel work | Grok Build **or** Goose subagents |
| GitHub / CI / external systems | Goose + MCP |
| Repeatable automation | Goose recipes |

---

## What to install on macOS

### Already covered (you have this)

| Item | Notes |
|------|-------|
| **Goose desktop app** | macOS app from [goose-docs.ai](https://goose-docs.ai/docs/getting-started/installation) |
| **Goose remote** | Use Goose’s server/API mode when you want sessions off the local machine |

Optional but useful with Goose:

```bash
# Goose CLI (terminal, recipes, scripting) — if not bundled with your install
# See: https://goose-docs.ai/docs/getting-started/installation
```

Configure providers in Goose (Settings → Providers), e.g. xAI for Grok:

```bash
export XAI_API_KEY="your-key"
# Example session:
goose session --model grok-3
```

Goose supports 15+ providers and reads project hints from `.goosehints` and `AGENT.md` / `AGENTS.md`.

---

### Still to install (recommended)

#### 1. Cursor IDE

- Download: [cursor.com](https://cursor.com)
- macOS app + optional shell command:

```bash
# From Cursor: Command Palette → "Install 'cursor' command in PATH"
cursor --version
```

Cursor is the interactive layer. Use:

- **Ask** — questions about the repo
- **Cmd+K** — small single-file edits
- **Agent / Composer** — multi-file work
- **Plan Mode (Shift+Tab)** — plan before code on non-trivial tasks

Project setup:

- `AGENTS.md` at repo root (shared rules)
- `.cursor/rules/*.mdc` for Cursor-only scoped rules (prefer over legacy `.cursorrules`)

#### 2. Grok Build CLI (optional but fits the stack)

Terminal agent from xAI; uses `grok-build-0.1` and reads `AGENTS.md`, MCP, hooks, skills.

```bash
curl -fsSL https://x.ai/cli/install.sh | bash
```

Requires **SuperGrok / X Premium Plus** (or similar) for the CLI product; the **model** is also available via xAI API for pay-as-you-go use in Goose or other harnesses.

Use Grok Build when you want:

- Plan → review → approve before execution
- Parallel subagents in git worktrees
- Headless runs in scripts (`-p`)

#### 3. Git (usually already present)

Needed for worktrees when running parallel agents:

```bash
git worktree add ../my-feature-worktree feature-branch
```

#### 4. MCP servers (as needed)

Connect tools to Goose and/or Cursor:

- GitHub, filesystem, browser, custom internal APIs
- Goose: Settings → MCP / extensions
- Cursor: MCP config in project or user settings

---

## Shared project configuration

Put these in every repo you work on with agents:

| File | Purpose | Read by |
|------|---------|---------|
| `AGENTS.md` | Build commands, architecture, test strategy, boundaries | Cursor, Grok Build, Goose, 20+ other agents |
| `.cursor/rules/*.mdc` | Cursor-specific globs (e.g. tests only) | Cursor |
| `.goosehints` | Goose-specific project hints | Goose |
| Goose **recipes** (YAML) | Repeatable automation (`goose run --recipe …`) | Goose |

Example `AGENTS.md` sections:

- How to install dependencies
- How to run tests and linters
- Folder layout and naming
- What agents must not change (secrets, generated files, etc.)

---

## Goose-specific notes (including remote)

Goose strengths for your setup:

- **Remote sessions** — desktop or API/server mode while code stays on your machine or a dev host
- **Provider-agnostic** — Grok via xAI, Claude, GPT, Ollama, etc.
- **Recipes & subrecipes** — version-controlled YAML workflows
- **Subagents** — quick parallel tasks; promote stable flows to subrecipes
- **MCP** — deepest integration story for GitHub, Slack, databases

Goose does **not** bill you itself when you bring your own API keys — usage counts against **each provider’s** quota (xAI, Anthropic, OpenAI, …).

Docs:

- [Goose introduction](https://goose-docs.ai/docs/tutorials/subagents/)
- [Subagents vs subrecipes](https://goose-docs.ai/docs/guides/recipes/subrecipes/)
- [GitHub: aaif-goose/goose](https://github.com/aaif-goose/goose)

---

## API limits and monitoring

You care about limits in **two different billing models**:

| Product | What limits | Where usage lives |
|---------|-------------|-------------------|
| **Cursor subscription** | Included agent/fast requests per month (tier-dependent) | Cursor account, not your LLM API key |
| **xAI / Grok API** | Pay-per-token when using `XAI_API_KEY` | xAI console |
| **Grok Build CLI subscription** | Product access (SuperGrok etc.), separate from raw API | xAI / X account |
| **Goose + BYOK** | Whatever the chosen provider charges | That provider’s console |

---

### Grok / xAI — CLI and API usage

**There is no widely documented, first-class “remaining quota” command in the Grok Build CLI** (as of mid-2026). Practical options:

#### 1. xAI Console (primary)

- [console.x.ai](https://console.x.ai) — API keys, usage, billing
- Check dashboard before long autonomous runs

#### 2. xAI API (programmatic)

Model reference: `grok-build-0.1` (~$1/M input, $2/M output tokens).  
Docs: [x.ai/news/grok-build-0.1](https://x.ai/news/grok-build-0.1)

You can script usage checks if xAI exposes billing/usage endpoints for your account (verify in current API docs):

```bash
# Illustrative — confirm endpoint in xAI docs for your account type
export XAI_API_KEY="your-key"
curl -s https://api.x.ai/v1/... \
  -H "Authorization: Bearer $XAI_API_KEY"
```

#### 3. Goose with xAI provider

When Goose uses `XAI_API_KEY`, **every token counts against xAI**, not Goose. Monitor at console.x.ai. Switch model in Goose per task (e.g. smaller/faster model for bulk work via subrecipes).

#### 4. Grok Build CLI subscription

CLI access may be gated on SuperGrok / X Premium — that limit is **subscription-based**, not the same as API token billing. Check your X / xAI account settings if the CLI refuses to run.

---

### Cursor — CLI usage

**Cursor does not offer a robust official CLI for “remaining credits this month.”** Usage is tied to your Cursor plan.

#### In the app (reliable)

- **Cursor → Settings → Subscription / Usage** (wording varies by version)
- Shows fast/slow requests and plan limits

#### CLI (`cursor` command)

The `cursor` CLI is mainly for **opening the editor** from the terminal, not quota reporting:

```bash
cursor --version
cursor .   # open current folder
```

For agent work from terminal, Cursor has been expanding **Cursor Agent CLI** / cloud agents — check current docs at [cursor.com/docs](https://cursor.com/docs) for your version. Do not assume a `cursor usage` subcommand exists until verified locally:

```bash
cursor --help
# If available in your build:
# cursor agent --help
```

#### Practical habit

Before large Agent/Composer runs:

1. Glance at in-app Usage
2. Prefer **Plan Mode** to avoid wasted requests on wrong approaches
3. Use **Goose/Grok with your own xAI key** for heavy batch work if Cursor quota is low

---

### Quick reference: who consumes what

```
Cursor Agent/Composer     →  Cursor subscription quota
Goose + XAI_API_KEY       →  xAI API billing
Goose + Anthropic key     →  Anthropic billing
Grok Build CLI (product)  →  SuperGrok / subscription (if applicable)
Grok Build / API model    →  xAI API billing (when using API key)
```

---

## Suggested macOS install checklist

- [x] Goose desktop app (+ remote as you prefer)
- [ ] Goose CLI (optional, for recipes/terminal)
- [ ] Cursor IDE + `cursor` in PATH
- [ ] Grok Build CLI (optional)
- [ ] `XAI_API_KEY` in env or Goose provider settings (if using Grok via API)
- [ ] `AGENTS.md` in active repos
- [ ] `.cursor/rules/` in active repos
- [ ] MCP servers you care about (GitHub, etc.)
- [ ] Bookmark [console.x.ai](https://console.x.ai) and Cursor in-app Usage

---

## Example workflow (one feature)

1. **Cursor Plan Mode** — “Add feature X; research repo; output plan only.”
2. Approve plan → implement in **Cursor Agent**.
3. **Grok Build** (parallel) — “Add unit tests for module Y in a worktree.”
4. **Goose recipe** — run tests, lint, open draft PR via GitHub MCP.
5. Final review and merge prep in **Cursor**.

---

## Pitfalls to avoid

- Running Cursor Agent, Goose, and Grok on the **same files simultaneously** — conflicts and overwrites
- Skipping **AGENTS.md** — each tool invents different conventions
- One giant prompt — split into plan → implement → verify
- Forgetting **two billing layers** — Cursor plan vs xAI API key vs Grok subscription

---

## References

| Topic | Link |
|-------|------|
| Cursor agent best practices | https://cursor.com/blog/agent-best-practices |
| Goose docs | https://goose-docs.ai |
| Goose GitHub | https://github.com/aaif-goose/goose |
| Grok Build CLI | https://x.ai/news/grok-build-cli |
| grok-build-0.1 API | https://x.ai/news/grok-build-0.1 |
| AGENTS.md cross-tool standard | https://agents.md |
| Goose vs Cursor (model switching) | https://tylerfolkman.substack.com/p/goose-vs-claude-code-vs-cursor-which |

---

## Open questions (verify on your machine)

These could not be fully verified in-session when tooling was interrupted; confirm locally:

```bash
goose --version
cursor --version
cursor --help
grok --version   # after Grok Build install
grok --help      # check for usage/billing subcommands
```

If xAI or Cursor add official CLI usage commands after this doc was written, prefer their docs over this file.

---

*Created: 2026-06-20 — research summary for personal dev workflow setup.*
