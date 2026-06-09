"""Quick verification script for /board help command."""
import ast
import json
import sys
sys.path.insert(0, '.')

print("=== Syntax check ===")
with open('tools.py') as f:
    ast.parse(f.read())
print("tools.py: syntax OK")
with open('__init__.py') as f:
    ast.parse(f.read())
print("__init__.py: syntax OK")

print("\n=== Import check ===")
from tools import board_help, board_help_slash
print(f"board_help: {type(board_help).__name__}")
print(f"board_help_slash: {type(board_help_slash).__name__}")

print("\n=== Output check ===")
r = board_help_slash('')
d = json.loads(r)
help_text = d['help']
print(f"output keys: {list(d.keys())}")
print(f"help length: {len(help_text)} chars")
print()

# Verify key content
assert "board-pull → board-status → board-plan → board-run-ready" in help_text, "Missing workflow"
assert "/board" in help_text, "Missing /board command"
assert "docs/hermes-plugin.md" in help_text, "Missing docs link"
assert "board-pull" in help_text, "Missing board-pull"
assert "board-status" in help_text, "Missing board-status"
assert "board-plan" in help_text, "Missing board-plan"
print("All assertions passed ✓")
print()
print(help_text)
