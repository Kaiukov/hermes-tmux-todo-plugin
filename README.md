# hermes-tmux-todo-board

**Bridge GitHub Issues → local task board → tmux-based AI coding agents**
(OpenCode, Codex, Claude).

A [Hermes Agent](https://hermes-agent.nousresearch.com) plugin that fetches
GitHub Issues into a local board, renders them as structured tasks, and
dispatches them to AI coding agents running in tmux windows. Works with any
Hermes terminal backend (local, Docker, SSH).

## Installation

```bash
hermes plugins install Kaiukov/hermes-tmux-todo-plugin
```

The plugin registers 6 tools and 6 slash commands automatically on the next
Hermes session start.

## Quick Start

```
/board-pull --repo owner/repo         (1) Fetch GitHub Issues
/board-status                          (2) See counts by status
/board-plan                            (3) List ready-to-go tasks
/board-run-ready limit=3 backend=opencode  (4) Dispatch to tmux agents
```

You can also call the underlying tools directly — `board_pull(...)`,
`board_plan(...)`, etc. — from code or in a tool-calling turn.

## Repo Structure

| Path | Purpose |
|------|---------|
| `plugin.yaml` | Hermes plugin manifest (name, version, tools, hooks) |
| `__init__.py` | `register(ctx)` — binds schemas → handlers on load |
| `schemas.py` | JSON schemas for each tool, shown to the LLM |
| `tools.py` | Handler functions, delegates to `bin/` scripts |
| `bin/board-pull` | Fetch GitHub Issues, cache locally |
| `bin/board-status` | Show task counts by status |
| `bin/board-plan` | List ready tasks for dispatch |
| `bin/board-next` | Pick the next ready task |
| `bin/board-sync` | Sync local status back to GitHub labels |
| `bin/board-config` | Read/write board configuration |
| `bin/board-add` | Add a task manually to the board |
| `runtime/tmux.py` | TmuxRuntimeAdapter — session lifecycle, prompt delivery, capture, silence-detection |
| `runtime/__init__.py` | Runtime package init |
| `runtime/_check.py` | Runtime health checks |
| `docs/hermes-plugin.md` | Full plugin documentation |
| `docs/file-roles.md` | File role descriptions |
| `docs/state-model.md` | State model and status enum |
| `skills/hermes-board-orchestrator/SKILL.md` | Orchestrator skill for board workflow |

## How It Works

1. **Pull** — `/board-pull` fetches GitHub Issues for a repo, using labels as
   status (`inbox` → `ready` → `in-progress` → `needs-review` →
   `blocked`/`needs-info` → `done`).
2. **Render** — A local board (`.tasks/board.json` + `TODO.md`) is created from
   the cached issues.
3. **Plan** — `/board-plan` lists ready tasks by priority.
4. **Dispatch** — `/board-run-ready` sends tasks to tmux windows running
   OpenCode, Codex, or Claude workers.
5. **Sync** — `/board-sync` pushes local status changes back to GitHub labels.

## Configuration

Board config lives at `.tasks/config.json` (auto-created if absent):

```json
{
  "default_repo": "owner/repo",
  "default_labels": "inbox,ready,in-progress,needs-review,blocked,needs-info,done",
  "default_backend": "opencode",
  "dispatch_limit": 2
}
```

Set `BOARD_REPO` env var to skip `--repo` on every command.

## Documentation

See [docs/hermes-plugin.md](docs/hermes-plugin.md) for the full plugin
documentation including architecture overview, comparison with the Claude
Code cmux-todo-plugin, and configuration reference.

## Requirements

- [Hermes Agent](https://hermes-agent.nousresearch.com) (CT 113+)
- tmux
- GitHub CLI (`gh`) authenticated
