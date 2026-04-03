import sys
from pathlib import Path

# Expose skill/scripts/ as importable modules for tests (rules, linter, fixers, models).
sys.path.insert(0, str(Path(__file__).parent / "skill" / "scripts"))
