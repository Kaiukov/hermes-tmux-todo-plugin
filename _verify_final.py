#!/usr/bin/env python3
"""Final verification for board_create_issue."""
import json, sys
sys.path.insert(0, '/root/hermes-tmux-todo-plugin')

# 1. Schema
from schemas import BOARD_CREATE_ISSUE
assert BOARD_CREATE_ISSUE['name'] == 'board_create_issue'
assert 'title' in BOARD_CREATE_ISSUE['parameters']['required']
print('1. Schema: OK')

# 2. Tool handler
from tools import board_create_issue, board_create_issue_slash, board_help, _get_default_repo
r = json.loads(board_create_issue({'title': ''}))
assert 'error' in r
r = json.loads(board_create_issue({'title': 'test'}))
assert 'error' in r  # no repo configured
r = json.loads(board_create_issue_slash('  my task  '))
assert 'error' in r
print('2. Handlers: OK')

# 3. Help text includes the new command
help_result = json.loads(board_help({}))
help_text = help_result.get('help', '')
assert '/board-create-issue' in help_text, 'Help missing board-create-issue'
print('3. Help text includes board-create-issue: OK')

# 4. Registration in __init__.py
src = open('/root/hermes-tmux-todo-plugin/__init__.py').read()
assert 'BOARD_CREATE_ISSUE' in src
assert 'board_create_issue_slash' in src
assert 'board-create-issue' in src
print('4. Registration in __init__.py: OK')

# 5. List all new registrations via inspection
for line in src.splitlines():
    if 'BOARD_CREATE_ISSUE' in line or 'board-create-issue' in line or 'board_create_issue' in line:
        print(f'   {line.strip()}')
print('5. Registrations visible: OK')

print('\n=== ALL CHECKS PASSED ===')
