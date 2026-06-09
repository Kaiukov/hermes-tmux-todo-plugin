import ast, sys
with open("runtime/tmux.py") as f:
    ast.parse(f.read())
print("Syntax OK")
sys.path.insert(0, ".")
from runtime.tmux import TmuxRuntimeAdapter
print("Import OK")
print(f"Lines: {len(open('runtime/tmux.py').readlines())}")
