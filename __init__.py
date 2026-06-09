"""
Hermes tmux TODO board plugin — GitHub Issues task board orchestrator.

Bridges GitHub Issues into a local .tasks/board.json + TODO.md,
then dispatches ready tasks to tmux-based coding agents (OpenCode, Codex, Claude).
"""
from pathlib import Path

_PLUGIN_DIR = Path(__file__).parent


def register(ctx):
    """Register tools, slash commands, CLI commands, and bundled skills."""
    from . import schemas, tools

    # --- Tools ---
    for schema, handler in [
        (schemas.BOARD_PULL, tools.board_pull),
        (schemas.BOARD_STATUS, tools.board_status),
        (schemas.BOARD_PLAN, tools.board_plan),
        (schemas.BOARD_RUN_READY, tools.board_run_ready),
        (schemas.BOARD_UPDATE_STATUS, tools.board_update_status),
        (schemas.BOARD_ADD_TASK, tools.board_add_task),
        (schemas.BOARD_RELEASE, tools.board_release),
        (schemas.BOARD_INIT, tools.board_init),
        (schemas.BOARD_CREATE_ISSUE, tools.board_create_issue),
    ]:
        ctx.register_tool(name=schema["name"], toolset="board", schema=schema, handler=handler)
    # --- Slash commands ---
    for name, handler in [
        ("board", tools.board_help_slash),
        ("board-pull", tools.board_pull_slash),
        ("board-status", tools.board_status_slash),
        ("board-plan", tools.board_plan_slash),
        ("board-run-ready", tools.board_run_ready_slash),
        ("board-update-status", tools.board_update_status_slash),
        ("board-add-task", tools.board_add_task_slash),
        ("board-create-issue", tools.board_create_issue_slash),
        ("board-release", tools.board_release_slash),
        ("board-init", tools.board_init_slash),
    ]:
        ctx.register_command(name=name, handler=handler)

    # --- Bundled skill ---
    skill_md = _PLUGIN_DIR / "skills" / "hermes-board-orchestrator" / "SKILL.md"
    if skill_md.exists():
        ctx.register_skill("hermes-board-orchestrator", skill_md)
