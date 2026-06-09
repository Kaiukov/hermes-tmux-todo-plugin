#!/usr/bin/env python3
"""Verify the new BOARD_CREATE_ISSUE code imports and works correctly."""
import json
import sys
sys.path.insert(0, '/root/hermes-tmux-todo-plugin')

from schemas import BOARD_CREATE_ISSUE, BOARD_PULL, BOARD_ADD_TASK
print('Schema name:', BOARD_CREATE_ISSUE['name'])
print('Required fields:', BOARD_CREATE_ISSUE['parameters']['required'])
assert BOARD_CREATE_ISSUE['name'] == 'board_create_issue'
assert 'title' in BOARD_CREATE_ISSUE['parameters']['required']

from tools import board_create_issue, board_create_issue_slash, _get_default_repo

# Test with no repo (should return error since no BOARD_REPO / config)
result = json.loads(board_create_issue({'title': 'test issue'}))
print('No-repo error result:', result)
assert 'error' in result

# Test with empty title
result = json.loads(board_create_issue({'title': ''}))
print('Empty-title result:', result)
assert 'error' in result

# Test slash handler delegates correctly
result = json.loads(board_create_issue_slash('  my new task  '))
print('Slash no-repo result:', result)
assert 'error' in result

# Verify default repo is empty (no BOARD_REPO set, no .tasks/config.json)
print('Default repo:', repr(_get_default_repo()))
assert _get_default_repo() == ''

# Verify registered in __init__.py
src = open('/root/hermes-tmux-todo-plugin/__init__.py').read()
assert 'BOARD_CREATE_ISSUE' in src
assert 'board_create_issue_slash' in src
assert 'board-create-issue' in src
print('Registration references found in __init__.py')

print('\n=== ALL CHECKS PASSED ===')
