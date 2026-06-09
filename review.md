# Review: /board-init, /board-create-issue, /board-release, /board

**Reviewer:** worker-opencode
**Date:** 2026-06-09
**Repo:** /root/hermes-tmux-todo-plugin

## Result: **PASS** — all 4 commands reviewed, no issues found.

---

## 1. schemas.py — Schema definitions

### BOARD_INIT (lines 158–170)
- ✅ Name: `board_init`
- ✅ Description: clear — explains it initializes repo with canonical labels, reads repo from .tasks/config.json or BOARD_REPO env, idempotent
- ✅ Parameters: empty object (correct — no args needed, repo auto-resolved)
- ✅ No `required` key (correct for empty params)

### BOARD_CREATE_ISSUE (lines 172–201)
- ✅ Name: `board_create_issue`
- ✅ Description: clear — creates GitHub issue with default 'inbox' label, repo resolution explained
- ✅ Parameters: `title` (required), `body` (optional), `labels` (optional), `repo` (optional)
- ✅ `required: ["title"]` — correct

### BOARD_RELEASE (lines 105–130)
- ✅ Name: `board_release`
- ✅ Description: clear — bump version, git tag, GitHub Release
- ✅ Parameters: `bump` (required, enum: patch/minor/major), `draft` (optional bool), `notes` (optional string)
- ✅ `required: ["bump"]` — correct
- ✅ All descriptions are LLM-clear: "patch (bug fixes), minor (features), major (breaking changes)"

**Verdict: PASS** — all schemas correct and well-described.

---

## 2. tools.py — Handler implementation

### board_init (lines 117–121)
- ✅ Calls `_run_bin("board-init")` with no args — correct, repo resolved by script
- ✅ Returns JSON string
- ✅ Verified at runtime: returns error dict when no repo configured — graceful fallback

### board_create_issue (lines 196–233)
- ✅ Validates title is not empty — returns error if missing
- ✅ Resolves repo: explicit arg → BOARD_REPO env → .tasks/config.json → error
- ✅ Builds `gh issue create` command with correct args
- ✅ Parses issue URL into number
- ✅ Catches: subprocess.TimeoutExpired, FileNotFoundError, generic Exception
- ✅ Returns JSON string

### board_release (lines 101–114)
- ✅ Calls `_run_bin("board-release")` with --bump, optional --draft, optional --notes
- ✅ Verified at runtime: returns error about uncommitted changes — working tree guard active

### board_help (lines 256–295)
- ✅ Returns formatted help text with workflow, commands table, usage examples
- ✅ Verified: 1834 chars of well-structured help
- ✅ Returns JSON string with "help" key

### board_init_slash (lines 151–153)
- ✅ Delegates to board_init({}) — correct, no params needed

### board_create_issue_slash (lines 235–237)
- ✅ Passes text as title — clean, title validation in parent handler handles empty input

### board_release_slash (lines 156–176)
- ✅ Parses bump type, validates enum (patch/minor/major)
- ✅ Detects --draft flag correctly
- ✅ Passes remaining text as notes
- ✅ Error on empty input
- ⚠️ **Minor note**: `remaining.remove("--draft")` removes only the first occurrence — acceptable since --draft appears at most once

### board_help_slash (lines 298–300)
- ✅ Delegates to board_help({})

### _get_default_repo (lines 179–193)
- ✅ Checks BOARD_REPO env, falls back to .tasks/config.json
- ✅ Handles JSON decode / IO errors gracefully

**Verdict: PASS** — all handlers return JSON strings, proper error handling, edge cases covered.

---

## 3. __init__.py — Registration

### Tool count: 9 ✅
| # | Schema | Handler |
|---|--------|---------|
| 1 | BOARD_PULL | board_pull |
| 2 | BOARD_STATUS | board_status |
| 3 | BOARD_PLAN | board_plan |
| 4 | BOARD_RUN_READY | board_run_ready |
| 5 | BOARD_UPDATE_STATUS | board_update_status |
| 6 | BOARD_ADD_TASK | board_add_task |
| 7 | BOARD_RELEASE | board_release |
| 8 | BOARD_INIT | board_init |
| 9 | BOARD_CREATE_ISSUE | board_create_issue |

### Slash command count: 10 ✅
| # | Name | Handler |
|---|------|---------|
| 1 | board | board_help_slash |
| 2 | board-pull | board_pull_slash |
| 3 | board-status | board_status_slash |
| 4 | board-plan | board_plan_slash |
| 5 | board-run-ready | board_run_ready_slash |
| 6 | board-update-status | board_update_status_slash |
| 7 | board-add-task | board_add_task_slash |
| 8 | board-create-issue | board_create_issue_slash |
| 9 | board-release | board_release_slash |
| 10 | board-init | board_init_slash |

All 4 new commands (board-init, board-create-issue, board-release, board) registered as both tools and slash commands.

**Verdict: PASS** — 9 tools + 10 commands as expected.

---

## 4. Verification — Import check

```
tools.py:                       syntax OK
schemas.py:                     syntax OK
__init__.py:                    syntax OK
Import:                         all handlers + helpers OK
board_help:                     1834 chars, valid JSON
board_init:                     error response (graceful — no repo configured)
board_create_issue empty title: error "title is required"
board_create_issue no repo:     error "no repo specified..."
board_release:                  error about uncommitted changes (working tree guard)
__init__ register():            import OK
```

**Verdict: PASS** — all imports work, error paths return proper JSON, handlers don't crash.

---

## 5. Hardcoded /tmp paths check

- `grep /tmp/ *.py` — zero results ✅
- Scripts use `Path(__file__).parent / "bin"` for vendored scripts ✅
- `_run_bin` uses `Path.cwd()` as working directory (workspace dir) ✅
- `_get_default_repo` uses `Path.cwd() / ".tasks" / "config.json"` (workspace dir) ✅
- No hardcoded paths anywhere ✅

**Verdict: PASS** — no hardcoded paths.

---

## Summary

| Check | Status |
|-------|--------|
| 1. Schema definitions | ✅ PASS |
| 2. Handler implementation | ✅ PASS |
| 3. Registration (9 tools + 10 commands) | ✅ PASS |
| 4. Import verification | ✅ PASS |
| 5. Hardcoded /tmp paths | ✅ PASS |

**Overall: PASS** — all 4 commands are correctly implemented, well-structured, and properly integrated.

### File changes summary
- `schemas.py` — BOARD_INIT, BOARD_CREATE_ISSUE, BOARD_RELEASE added (no issues)
- `tools.py` — board_init, board_create_issue, board_release, board_help + slash handlers added (no issues)
- `__init__.py` — all 9 tools + 10 commands registered (count correct)
- `bin/board-init` — created by parent task ✅ (exists)
- `bin/board-release` — created by parent task ✅ (exists)
