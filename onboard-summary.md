# /board-onboard Slash Command — Summary

## What was done

Added `/board-onboard` slash command to the Hermes tmux TODO board plugin.

## Changes

### `tools.py`
- Added `"board-onboard"` entry to `_COMMANDS_HELP` dict (descriptive text shown in `/board` help)
- Added `_BOARD_ONBOARD_HELP` constant — formatted onboarding text with:
  - "To start orchestrating: /skill hermes-board-orchestrator"
  - Workflow overview: board-pull → board-status → board-plan → board-run-ready
  - Available model tiers: flash (worker-flash), general (worker-opencode), pro (worker-pro)
  - Operating rules summary
- Added `board_onboard(args)` handler — returns JSON with the help text
- Added `board_onboard_slash(text)` handler — slash entry point

### `__init__.py`
- Registered `"board-onboard"` → `tools.board_onboard_slash` in the slash commands list

## Files changed
- `/root/hermes-tmux-todo-plugin/tools.py` — +50 lines
- `/root/hermes-tmux-todo-plugin/__init__.py` — +1 line

## Verification
- Python syntax validated (lint passed on both files)
- Pattern follows existing slash command convention (board_init / board_init_slash pattern)
- No tool schema needed — it's pure info/setup
