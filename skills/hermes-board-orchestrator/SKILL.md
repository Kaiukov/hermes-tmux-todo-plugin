---
name: hermes-board-orchestrator
description: Teach the orchestrator Hermes agent how to use the tmux-GitHub task board — pull GitHub issues, plan, dispatch to AI workers in tmux panes, and sync status back.
version: 1.0.0
platforms: [linux]
metadata:
  hermes:
    tags: [board, orchestrator, tmux, github, tasks]
    related_skills: [kanban-worker]
---

# Hermes Board Orchestrator Skill

> For the **orchestrator** agent that reads the board, plans, and dispatches
> ready tasks to workers in tmux panes (OpenCode/Codex/Claude). Not for workers.

## Overview

`hermes-tmux-todo-board` bridges GitHub Issues and tmux-based AI coding agents.
The orchestrator runs a **pull → plan → dispatch → sync** loop:

1. **Pull**: fetch GitHub issues, render local board
2. **Status**: check counts by status
3. **Plan**: pick ready tasks, decide parallel dispatch
4. **Run**: launch workers in tmux windows, send prompts
5. **Sync**: mark tasks done, push status back to GitHub labels

## Sources of Truth

| Source | Role | Mutability |
|---|---|---|
| **GitHub labels** | Authoritative status (inbox→ready→in-progress→needs-review→done) | External source |
| `.tasks/board.json` | Local derived cache, merged view. Never hand-edited | Regenerated |
| `TODO.md` | Human-readable board, auto-generated. Never hand-edited | Regenerated |
| `.tasks/local.json` | Local-only tasks not pushed to GitHub | Hand-edited via tool |
| `.tasks/issues/<n>.md` | Per-issue body cache | Regenerated |
| `runtime/tmux.py` | TmuxRuntimeAdapter — agent lifecycle | Code |

## Workflow

### 1. Board-Pull
```
board_pull(repo="owner/repo", labels="inbox,ready,...", assignee="user")
```
→ fetches GitHub issues → auto-runs board-render → `.tasks/board.json` + `TODO.md`

### 2. Board-Status
```
board_status()
```
→ compact counts: `inbox=2  ready=5  in-progress=1  blocked=0` + `next_ready`

### 3. Board-Plan
```
board_next --status ready --json
```
→ first ready task as JSON `{number, title, url, labels, assignees}`
→ read body from `.tasks/issues/<n>.md` for context

### 4. Board-Run-Ready
```
board_run_ready(limit=2, backend="opencode", issue_numbers=[42, 99])
```
→ calls `TmuxRuntimeAdapter.open_worker()` per task, creates tmux window,
sends compact prompt, waits for monitor-silence

### 5. Board-Sync (Completion)
```
board_update_status(issue=42, status="needs-review")
```
→ swaps canonical label on GitHub (idempotent), re-renders board locally

### 6. Board-Add (Local Tasks)
```
board_add_task(title="fix login CSS")
```
→ appends to `.tasks/local.json`, re-renders board

## Concurrency Rules

- **One orchestrator** reads the board and plans at a time.
- **Multiple workers** run in parallel in separate tmux windows (default limit 2).
- The orchestrator only marks tasks `in-progress` one at a time.
- Real parallelism is managed by tmux monitor-silence, not the task list:
  you can launch multiple workers while the board shows one `in-progress`.

## Worker Prompt Template (Compact, Delegation-First)

When dispatching to a tmux pane, send a compact self-contained prompt:

```
Task: <title>
Context: <3-5 lines>
Repo: owner/repo  Branch: feature/N
Steps:
1. <step>
Deliverable: <one sentence>
Keep under N tokens. Commit on finish.
```

The worker runs autonomously in its own tmux window. Do NOT send the full
board, conversation history, or chatty instructions.

## Completion Feedback Loop

1. Worker finishes → tmux monitor-silence triggers.
2. Run `capture_tail()` to grab output (last 40 lines).
3. If accepted: `board_update_status(issue=N, status="needs-review")` + optional `kanban_create` for review.
4. If rejected: fix prompt, re-dispatch, or reset to `status="ready"`.
5. Re-pull board: `board_pull()` to refresh.

For local tasks: `board-add --set L3 --status done` or `board-add --remove L3`.

## Pitfalls

**Don't dispatch the same task twice.** Check `in-progress` status before
calling `board_run_ready()`.

**monitor-silence can false-fire.** A worker idle mid-task appears "done."
Always capture tail output and verify before updating status.

**GitHub labels are the source of truth.** Always run `board_pull()` after
long absences or if another operator may have touched the board.

**Concurrent workers share a tmux session.** Use distinct window names
(`open_worker()` auto-sanitizes). Don't kill the session while active.

**Worker prompts must be self-contained.** The tmux worker has no access to
your conversation — include repo, branch, and acceptance criteria.
