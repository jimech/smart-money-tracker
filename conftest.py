import sys
from pathlib import Path

# Ensure the repo root is importable so `from smart_money import ...` works
# no matter how pytest is invoked.
sys.path.insert(0, str(Path(__file__).resolve().parent))
