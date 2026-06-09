"""
Tool handlers — the code that runs when the LLM calls board tools.

All handlers receive args (dict) and return JSON strings.
Vendored board scripts live in bin/ and are called via subprocess.
"""
import json
import os
import subprocess
import sys
from pathlib import Path

_PLUGIN_DIR = Path(__file__).parent
_BIN = _PLUGIN_DIR / "bin"


def _json(obj: dict) -> str:
    """json.dumps with ensure_ascii=False so box-drawing chars render correctly."""
    return json.dumps(obj, ensure_ascii=False)


def _run_bin(script: str, *args: str) -> dict:
    """Run a vendored bin/ script and return parsed JSON stdout, or error dict."""
    script_path = _BIN / script
    if not script_path.exists():
        return {"error": f"script not found: {script}"}
    try:
        result = subprocess.run(
            [str(script_path), *args],
            capture_output=True, text=True, timeout=120,
            cwd=Path.cwd(),
        )
        if result.returncode != 0:
            return {"error": result.stderr.strip() or f"exit code {result.returncode}"}
        # Try JSON from stdout, fall back to combined stdout+stderr text
        output = (result.stdout + result.stderr).strip()
        try:
            return json.loads(result.stdout or result.stderr)
        except json.JSONDecodeError:
            return {"output": output} if output else {"output": "ok (no output)"}
    except subprocess.TimeoutExpired:
        return {"error": "timeout after 120s"}
    except Exception as e:
        return {"error": str(e)}


def board_pull(args: dict, **kwargs) -> str:
    """Fetch GitHub Issues → .tasks/issues.json → board.json + TODO.md."""
    repo = args.get("repo", "") or _get_default_repo()
    labels = args.get("labels", "")
    assignee = args.get("assignee", "")

    cmd_args = ["--repo", repo]
    if labels:
        cmd_args += ["--label", labels]
    if assignee:
        cmd_args += ["--assignee", assignee]

    result = _run_bin("board-pull", *cmd_args)
    return _json(result)


def board_status(args: dict, **kwargs) -> str:
    """Compact board summary — counts only."""
    result = _run_bin("board-status")
    return _json(result)


def board_plan(args: dict, **kwargs) -> str:
    """Return ready tasks in compact format."""
    result = _run_bin("board-next", "--all-ready")
    return _json(result)


def board_run_ready(args: dict, **kwargs) -> str:
    """Dispatch ready tasks to tmux panes."""
    limit = args.get("limit", 2)
    backend = args.get("backend", "opencode")
    issue_numbers = args.get("issue_numbers", [])

    # TODO: implement tmux dispatch via runtime/tmux.py
    return _json({
        "dispatched": [],
        "note": "tmux dispatch not yet implemented — see runtime/tmux.py",
        "limit": limit,
        "backend": backend,
    })


def board_update_status(args: dict, **kwargs) -> str:
    """Update task status locally and sync to GitHub labels."""
    issue = args.get("issue", 0)
    status = args.get("status", "")
    result = _run_bin("board-sync", "--issue", str(issue), "--status", status)
    return _json(result)


def board_add_task(args: dict, **kwargs) -> str:
    """Add a local-only task."""
    title = args.get("title", "")
    body = args.get("body", "")
    status = args.get("status", "ready")
    result = _run_bin("board-add", "--title", title, "--body", body, "--status", status)
    return _json(result)


def board_release(args: dict, **kwargs) -> str:
    """Bump version, tag, and create GitHub Release."""
    bump = args.get("bump", "patch")
    draft = args.get("draft", False)
    notes = args.get("notes", "")

    cmd_args = ["--bump", bump]
    if draft:
        cmd_args.append("--draft")
    if notes:
        cmd_args += ["--notes", notes]

    result = _run_bin("board-release", *cmd_args)
    return _json(result)


def board_init(args: dict, **kwargs) -> str:
    """Initialize GitHub repo with canonical board labels."""
    repo = args.get("repo", "") or _get_default_repo()
    cmd_args = []
    if repo:
        cmd_args = ["--repo", repo]
    result = _run_bin("board-init", *cmd_args)
    return _json(result)


# --- Slash command handlers (called via /board-*) ---
# These parse the slash command text and call the corresponding tool handler.

def board_pull_slash(text: str, **kwargs) -> str:
    return board_pull({"repo": text.strip()})

def board_status_slash(text: str, **kwargs) -> str:
    return board_status({})

def board_plan_slash(text: str, **kwargs) -> str:
    return board_plan({})

def board_run_ready_slash(text: str, **kwargs) -> str:
    parts = text.strip().split()
    limit = int(parts[0]) if parts and parts[0].isdigit() else 2
    return board_run_ready({"limit": limit})

def board_update_status_slash(text: str, **kwargs) -> str:
    parts = text.strip().split()
    if len(parts) >= 2:
        return board_update_status({"issue": int(parts[0]), "status": parts[1]})
    return _json({"error": "usage: /board-update-status <issue> <status>"})

def board_add_task_slash(text: str, **kwargs) -> str:
    return board_add_task({"title": text.strip()})


def board_init_slash(text: str, **kwargs) -> str:
    """Initialize GitHub repo with canonical board labels."""
    repo = text.strip()
    return board_init({"repo": repo} if repo else {})


def board_release_slash(text: str, **kwargs) -> str:
    """Parse /board-release args: bump type, optional --draft, optional notes."""
    parts = text.strip().split()
    if not parts:
        return _json({"error": "usage: /board-release <patch|minor|major> [--draft] [<notes>]"})

    bump = parts[0].lower()
    if bump not in ("patch", "minor", "major"):
        return _json({"error": f"invalid bump type '{bump}'. Use patch, minor, or major."})

    args = {"bump": bump}
    remaining = parts[1:]

    if "--draft" in remaining:
        args["draft"] = True
        remaining.remove("--draft")

    if remaining:
        args["notes"] = " ".join(remaining)

    return board_release(args)


def _get_default_repo() -> str:
    """Resolve default repo from BOARD_REPO env, .tasks/config.json, or git remote."""
    env_repo = os.environ.get("BOARD_REPO")
    if env_repo:
        return env_repo
    config_path = Path.cwd() / ".tasks" / "config.json"
    if config_path.exists():
        try:
            config = json.loads(config_path.read_text())
            repo = config.get("repo", "")
            if repo:
                return repo
        except (json.JSONDecodeError, IOError):
            pass
    # Fallback: auto-detect from git remote
    try:
        result = subprocess.run(
            ["git", "remote", "get-url", "origin"],
            capture_output=True, text=True, timeout=5,
            cwd=Path.cwd(),
        )
        if result.returncode == 0:
            url = result.stdout.strip()
            # Extract owner/repo from GitHub URL
            # https://github.com/owner/repo.git → owner/repo
            # git@github.com:owner/repo.git → owner/repo
            import re
            m = re.search(r'github\.com[:/](.+?)/(.+?)(?:\.git)?$', url)
            if m:
                return f"{m.group(1)}/{m.group(2)}"
    except Exception:
        pass
    return ""


def board_create_issue(args: dict, **kwargs) -> str:
    """Create a GitHub issue via `gh issue create`."""
    title = args.get("title", "").strip()
    if not title:
        return _json({"error": "title is required"})

    repo = args.get("repo", "") or _get_default_repo()
    if not repo:
        return _json({"error": "no repo specified and BOARD_REPO / .tasks/config.json not set"})

    labels = args.get("labels", "inbox")
    body = args.get("body", "")

    cmd = ["gh", "issue", "create", "--repo", repo, "--title", title, "--label", labels]
    if body:
        cmd += ["--body", body]

    try:
        result = subprocess.run(
            cmd, capture_output=True, text=True, timeout=120,
        )
        if result.returncode != 0:
            return _json({"error": result.stderr.strip() or f"exit code {result.returncode}"})
        url = result.stdout.strip()
        # gh outputs: https://github.com/owner/repo/issues/123
        number = url.rstrip("/").rsplit("/", 1)[-1] if url else ""
        try:
            number = int(number)
        except (ValueError, TypeError):
            number = 0
        return _json({"number": number, "url": url})
    except subprocess.TimeoutExpired:
        return _json({"error": "timeout after 120s"})
    except FileNotFoundError:
        return _json({"error": "gh CLI not found — install GitHub CLI (gh)"})
    except Exception as e:
        return _json({"error": str(e)})


def board_create_issue_slash(text: str, **kwargs) -> str:
    """Parse --repo flag and title from slash text, then create a GitHub issue."""
    parts = text.strip().split()
    repo = ""
    title_parts = []
    i = 0
    while i < len(parts):
        if parts[i] == "--repo" and i + 1 < len(parts):
            repo = parts[i + 1]
            i += 2
        else:
            title_parts.append(parts[i])
            i += 1
    title = " ".join(title_parts)
    args = {"title": title}
    if repo:
        args["repo"] = repo
    return board_create_issue(args)


# --- /board help command (slash-only, no tool schema) ---

_COMMANDS_HELP = {
    "board-pull": "Fetch GitHub Issues for a repo and render the local task board",
    "board-status": "Show compact board summary — counts by status",
    "board-plan": "List ready tasks available for dispatch",
    "board-run-ready": "Dispatch ready tasks to tmux-based coding agents",
    "board-update-status": "Update a task's status locally and sync to GitHub labels",
    "board-add-task": "Add a local-only task (not a GitHub issue)",
    "board-create-issue": "Create a GitHub issue from a description",
    "board-release": "Bump version, tag, and publish a GitHub Release",
    "board-init": "Initialize GitHub repo with canonical board labels",
    "board": "Show this help screen and workflow overview",
    "board-onboard": "Show orchestrator onboarding instructions",
}


def board_help(args: dict, **kwargs) -> str:
    """Return formatted help text with workflow overview and available commands."""
    lines = [
        "╔══════════════════════════════════════════╗",
        "║   Hermes Tmux TODO Board — Help         ║",
        "╚══════════════════════════════════════════╝",
        "",
        "Workflow:",
        "  board-pull → board-status → board-plan → board-run-ready",
        "",
        "  1. board-pull       — fetch issues from GitHub, build local board",
        "  2. board-status     — see what's available (counts by status)",
        "  3. board-plan       — pick which ready tasks to dispatch",
        "  4. board-run-ready  — send tasks to tmux coding agents",
        "",
        "Available commands:",
    ]

    for name, desc in _COMMANDS_HELP.items():
        lines.append(f"  /{name:<20} {desc}")

    lines.extend([
        "",
        "Documentation:",
        "  docs/hermes-plugin.md  — full plugin documentation",
        "",
        "Usage:",
        "  /board                       — show this help",
        '  /board-pull <owner/repo>     — fetch issues from a repo',
        "  /board-status                — quick board snapshot",
        "  /board-plan                  — list ready tasks",
        '  /board-run-ready [limit]     — dispatch N tasks (default 2)',
        '  /board-update-status <n> <s> — set issue N to status s',
        '  /board-add-task <title>      — add a local todo',
        '  /board-create-issue <title>  — create a GitHub issue',
        '  /board-release <bump> [--draft] [notes] — cut a new release',
        '  /board-init                   — init repo with canonical labels',
    ])

    return _json({"help": "\n".join(lines)})


def board_help_slash(text: str, **kwargs) -> str:
    """Slash handler for /board — returns formatted help."""
    return board_help({})


# --- /board-onboard command (slash-only, no tool schema) ---

_BOARD_ONBOARD_HELP = """\
╔══════════════════════════════════════════════════════════╗
║   Hermes Board — ORCHESTRATOR MODE ACTIVATED             ║
╚══════════════════════════════════════════════════════════╝

You are now the ORCHESTRATOR. Load the hermes-board-orchestrator skill
and follow these rules immediately:

WORKFLOW: board-pull → board-status → board-plan → board-run-ready

RULES:
  • Do NOT implement code yourself — delegate EVERYTHING to workers.
  • Use kanban_create() with --assignee=<model-name> for each task.
  • Max 2 workers in flight (kanban.max_in_progress_per_profile=2).
  • Hard gate: independently verify every worker output — never trust self-report.
  • Review pipeline: implement → review → orchestrator-verify.
  • Dispatch specs in worker workspace, never /tmp.

MODEL TIERS (use as --assignee):
  deepseek-v4-flash  — general work (opencode-go)
  deepseek-v4-pro    — complex implementation (opencode-go)

SLASH COMMANDS:
  /board-pull <repo>     — fetch issues from GitHub
  /board-status          — compact counts
  /board-plan            — list ready tasks
  /board-run-ready [N]   — dispatch N tasks to workers
  /board-update-status   — change status + sync labels
  /board-create-issue    — create GitHub issue
  /board-release         — bump version + tag + release
  /board-init            — init repo with canonical labels
  /board                 — full command reference

START: run /board-pull <owner/repo> to fetch the board, then /board-status."""


def board_onboard(args: dict, **kwargs) -> str:
    """Return formatted orchestrator onboarding instructions."""
    return _json({"help": _BOARD_ONBOARD_HELP.strip()})


def board_onboard_slash(text: str, **kwargs) -> str:
    """Slash handler for /board-onboard."""
    return board_onboard({})

