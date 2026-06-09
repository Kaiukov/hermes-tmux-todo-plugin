"""
Tool handlers — the code that runs when the LLM calls board tools.

All handlers receive args (dict) and return JSON strings.
Vendored board scripts live in bin/ and are called via subprocess.
"""
import json
import subprocess
import sys
from pathlib import Path

_PLUGIN_DIR = Path(__file__).parent
_BIN = _PLUGIN_DIR / "bin"


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
        # Try JSON, fall back to plain text
        try:
            return json.loads(result.stdout)
        except json.JSONDecodeError:
            return {"output": result.stdout.strip()}
    except subprocess.TimeoutExpired:
        return {"error": "timeout after 120s"}
    except Exception as e:
        return {"error": str(e)}


def board_pull(args: dict, **kwargs) -> str:
    """Fetch GitHub Issues → .tasks/issues.json → board.json + TODO.md."""
    repo = args.get("repo", "")
    labels = args.get("labels", "")
    assignee = args.get("assignee", "")

    cmd_args = ["--repo", repo]
    if labels:
        cmd_args += ["--label", labels]
    if assignee:
        cmd_args += ["--assignee", assignee]

    result = _run_bin("board-pull", *cmd_args)
    return json.dumps(result)


def board_status(args: dict, **kwargs) -> str:
    """Compact board summary — counts only."""
    result = _run_bin("board-status")
    return json.dumps(result)


def board_plan(args: dict, **kwargs) -> str:
    """Return ready tasks in compact format."""
    result = _run_bin("board-next", "--all-ready")
    return json.dumps(result)


def board_run_ready(args: dict, **kwargs) -> str:
    """Dispatch ready tasks to tmux panes."""
    limit = args.get("limit", 2)
    backend = args.get("backend", "opencode")
    issue_numbers = args.get("issue_numbers", [])

    # TODO: implement tmux dispatch via runtime/tmux.py
    return json.dumps({
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
    return json.dumps(result)


def board_add_task(args: dict, **kwargs) -> str:
    """Add a local-only task."""
    title = args.get("title", "")
    body = args.get("body", "")
    status = args.get("status", "ready")
    result = _run_bin("board-add", "--title", title, "--body", body, "--status", status)
    return json.dumps(result)


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
    return json.dumps({"error": "usage: /board-update-status <issue> <status>"})

def board_add_task_slash(text: str, **kwargs) -> str:
    return board_add_task({"title": text.strip()})
