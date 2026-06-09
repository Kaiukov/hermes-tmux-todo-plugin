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
