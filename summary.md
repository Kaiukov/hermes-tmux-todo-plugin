# /board-init command — Task Summary

## What was done

Added `/board-init` slash command that initializes a GitHub repo with canonical board labels.

## Artifacts

### Created
- **bin/board-init** — shell script that uses `gh label create`/`gh label edit` to create/update canonical labels:
  - inbox, ready, in-progress, needs-review, blocked, needs-info, done
  - Reads repo from `--repo` flag, `BOARD_REPO` env, or `.tasks/config.json board_repo` key
  - Outputs JSON summary: `{repo, labels_created, labels_skipped, errors}`

### Modified
- **schemas.py** — added `BOARD_INIT` schema (no parameters, repo read from config/env)
- **tools.py** — added `board_init()` handler (calls `bin/board-init`), `board_init_slash()` slash handler, updated `_COMMANDS_HELP` dict and usage section
- **__init__.py** — registered `BOARD_INIT` tool + `board-init` slash command
- **plugin.yaml** — added `board_init` to `provides_tools`

## Verification

All imports pass:
- `from schemas import BOARD_INIT` → OK
- `from tools import board_init, board_init_slash` → OK
- `import __init__` → OK
- Schema has empty parameters (correct — repo read from config/env)
- `BOARD_INIT` registered in `register()` tools list
- `board-init` registered in `register()` slash commands list
- `board_init_slash("")` runs without errors (returns error when no repo configured, correct behavior)
