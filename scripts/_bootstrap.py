"""Import this first in every script in this folder.

Lets scripts be run directly (VS Code "Run Python File", `python scripts/x.py`)
without requiring `pip install -e .` first, while still working fine if that
was done.
"""

from __future__ import annotations

import sys
from pathlib import Path

_SRC = Path(__file__).resolve().parents[1] / "src"
if str(_SRC) not in sys.path:
    sys.path.insert(0, str(_SRC))
