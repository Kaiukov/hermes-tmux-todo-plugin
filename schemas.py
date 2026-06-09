"""
Tool schemas — what the LLM sees to decide when to call board tools.
"""

BOARD_PULL = {
    "name": "board_pull",
    "description": (
        "Fetch GitHub Issues for a repo and render the local task board "
        "(.tasks/issues.json → .tasks/board.json + TODO.md). "
        "Use this to refresh the board from GitHub before planning or dispatching."
    ),
    "parameters": {
        "type": "object",
        "properties": {
            "repo": {
                "type": "string",
                "description": "GitHub repo as owner/repo (e.g. 'Kaiukov/hermes-tmux-todo-plugin')",
            },
            "labels": {
                "type": "string",
                "description": "Comma-separated labels to filter by (default: inbox,ready,in-progress,needs-review,blocked,needs-info,done)",
            },
            "assignee": {
                "type": "string",
                "description": "Filter by GitHub assignee username",
            },
        },
        "required": ["repo"],
    },
}

BOARD_STATUS = {
    "name": "board_status",
    "description": (
        "Return a compact board summary: total tasks, counts by status (ready, in_progress, blocked, needs_review). "
        "No full TODO dump — just counts. Use this before planning to see what's available."
    ),
    "parameters": {
        "type": "object",
        "properties": {},
    },
}

BOARD_PLAN = {
    "name": "board_plan",
    "description": (
        "Return ready tasks from the board in compact format: [{number, title, url}]. "
        "Only tasks with status 'ready' are returned. Use this to decide what to dispatch."
    ),
    "parameters": {
        "type": "object",
        "properties": {},
    },
}

BOARD_RUN_READY = {
    "name": "board_run_ready",
    "description": (
        "Dispatch ready tasks to tmux-based coding agents (OpenCode, Codex, or Claude). "
        "Creates tmux windows, sends compact worker prompts, returns dispatch summary. "
        "Limit concurrency with the 'limit' parameter (default 2)."
    ),
    "parameters": {
        "type": "object",
        "properties": {
            "limit": {
                "type": "integer",
                "description": "Max tasks to dispatch (default: 2)",
            },
            "backend": {
                "type": "string",
                "description": "Worker backend: opencode (default), codex, or claude",
            },
            "issue_numbers": {
                "type": "array",
                "items": {"type": "integer"},
                "description": "Specific issue numbers to dispatch (omit to dispatch next ready tasks)",
            },
        },
    },
}

BOARD_UPDATE_STATUS = {
    "name": "board_update_status",
    "description": (
        "Update a task's status locally and sync to GitHub labels. "
        "Status must be one of: inbox, ready, in-progress, needs-review, blocked, needs-info, done."
    ),
    "parameters": {
        "type": "object",
        "properties": {
            "issue": {
                "type": "integer",
                "description": "GitHub issue number",
            },
            "status": {
                "type": "string",
                "description": "New status (inbox, ready, in-progress, needs-review, blocked, needs-info, done)",
            },
        },
        "required": ["issue", "status"],
    },
}

BOARD_RELEASE = {
    "name": "board_release",
    "description": (
        "Bump the plugin version, create git tag, and publish a GitHub Release. "
        "Use this after completing a milestone or batch of tasks to cut a release."
    ),
    "parameters": {
        "type": "object",
        "properties": {
            "bump": {
                "type": "string",
                "enum": ["patch", "minor", "major"],
                "description": "Semver bump type: patch (bug fixes), minor (features), major (breaking changes)",
            },
            "draft": {
                "type": "boolean",
                "description": "Create release as draft (not yet published). Default: false",
            },
            "notes": {
                "type": "string",
                "description": "Optional release notes text. If omitted, auto-generates from git log since last tag.",
            },
        },
        "required": ["bump"],
    },
}

BOARD_ADD_TASK = {
    "name": "board_add_task",
    "description": (
        "Add a local-only task (not a GitHub issue) to .tasks/local.json. "
        "Use for quick todos that don't need GitHub tracking."
    ),
    "parameters": {
        "type": "object",
        "properties": {
            "title": {
                "type": "string",
                "description": "Task title",
            },
            "body": {
                "type": "string",
                "description": "Optional task description",
            },
            "status": {
                "type": "string",
                "description": "Initial status (default: ready)",
            },
        },
        "required": ["title"],
    },
}

BOARD_INIT = {
    "name": "board_init",
    "description": (
        "Initialize a GitHub repo with canonical board labels "
        "(inbox, ready, in-progress, needs-review, blocked, needs-info, done). "
        "Repo is read from .tasks/config.json (board_repo key) or BOARD_REPO env var. "
        "Idempotent — skips labels that already exist."
    ),
    "parameters": {
        "type": "object",
        "properties": {},
    },
}

BOARD_CREATE_ISSUE = {
    "name": "board_create_issue",
    "description": (
        "Create a GitHub issue in the configured repo. "
        "The issue gets default label 'inbox'. "
        "Use this to create new tasks directly on GitHub."
    ),
    "parameters": {
        "type": "object",
        "properties": {
            "title": {
                "type": "string",
                "description": "Issue title (required)",
            },
            "body": {
                "type": "string",
                "description": "Optional issue body / description",
            },
            "labels": {
                "type": "string",
                "description": "Comma-separated labels (default: inbox)",
            },
            "repo": {
                "type": "string",
                "description": "GitHub repo as owner/repo. Defaults to BOARD_REPO env or .tasks/config.json",
            },
        },
        "required": ["title"],
    },
}
