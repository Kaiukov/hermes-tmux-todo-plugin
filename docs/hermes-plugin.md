# hermes-tmux-todo-board

Bridge GitHub Issues → local task board → tmux-based AI coding agents
(OpenCode, Codex, Claude).

This is a Hermes plugin — install it with one command, then orchestrate
GitHub issues from slash commands and tools inside your Hermes session.

## What it does

1. **Pull** GitHub Issues for a repo, using labels as status (`inbox` →
   `ready` → `in-progress` → `needs-review` → `blocked` / `needs-info` → `done`).
2. **Render** a local board (`.tasks/board.json` + `TODO.md`) from the cached
   issues.
3. **Plan** by listing ready tasks.
4. **Dispatch** ready tasks to tmux windows running OpenCode, Codex, or Claude.

Status flows both ways: pull issues in, work locally, sync status back to
GitHub labels (`board-sync`).

## Claude Code cmux-todo-plugin mirror

This plugin is a straight port of the Claude Code
[cmux-todo-plugin](https://github.com/nicholasgriffintn/cmux-todo-plugin)
workflow — same vendored board scripts (`bin/board-*`), same state model
(canonical status enum, four representations, bidirectional sync), same
session-recovery procedure.

The key difference: **tmux-first, not cmux**. The Claude plugin uses
`cmux` (Claude's built-in multi-pane); this one orchestrates standard tmux
windows. It works with any Hermes terminal backend (local, Docker, SSH).

## Installation

```bash
hermes plugins install Kaiukov/hermes-tmux-todo-plugin
```

The plugin registers itself on the next Hermes session start. You get 6
tools and 6 slash commands automatically.

## Quick start

```
/board-pull --repo Kaiukov/my-project        (1) Fetch GitHub Issues
/board-status                                 (2) See counts by status
/board-plan                                   (3) List ready-to-go tasks
/board-run-ready limit=3 backend=opencode     (4) Dispatch to tmux agents
```

You can also call the underlying tools directly (`board_pull(...)`,
`board_plan(...)`, etc.) from code or in a tool-calling turn.

## Architecture

```
plugin.yaml          — manifest (name, version, tools, hooks)
__init__.py          — register(ctx): binds schemas → handlers
schemas.py           — tool JSON schemas the LLM sees
tools.py             — handler functions, delegates to bin/ scripts
bin/board-*          — 7 vendored bash scripts (pull, render, status,
                       next, sync, config, add)
runtime/tmux.py      — TmuxRuntimeAdapter: session lifecycle, prompt
                       delivery, capture, silence-detection
```

The Python layer is thin — tools.py calls `subprocess.run()` on the
vendored bash scripts, which do the real work (GitHub API, file I/O,
board rendering). The tmux runtime is pure Python with `subprocess`
calls to `tmux(1)`.

## Differences from Claude Code cmux-todo-plugin

| Aspect          | Claude (cmux)                    | Hermes (this plugin)         |
|-----------------|-----------------------------------|------------------------------|
| Runtime         | cmux (Claude multi-pane)          | Standard tmux sessions       |
| Prompt delivery | Claude TUI interaction            | send-keys -l literal mode    |
| Completion      | Agent signals done in chat        | monitor-silence detection    |
| Backends        | Claude only                       | OpenCode, Codex, Claude      |
| Installation    | Manual clone + cmux config        | `hermes plugins install`     |
| Siblings        | Claude-only tool ecosystem        | Works with kanban tools,     |
|                 |                                   | delegate_task, cron, etc.    |

The vendored board scripts are identical in behaviour. The tmux adapter
(`runtime/tmux.py`) replaces what cmux provided — it launches workers in
tmux windows, sends prompts in literal mode (no shell interpretation),
chunks long text at 1000 chars, and polls `monitor-silence` to detect
when a worker finishes.

## Configuration

`.tasks/config.json` — optional, created automatically if absent:

```json
{
  "default_repo": "owner/repo",
  "default_labels": "inbox,ready,in-progress,needs-review,blocked,needs-info,done",
  "default_backend": "opencode",
  "dispatch_limit": 2
}
```

Set `BOARD_REPO` env var to skip `--repo` on every command. Labels,
assignee, and milestone filter at pull time.
