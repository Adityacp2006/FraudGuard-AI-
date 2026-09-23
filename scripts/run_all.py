"""Run every Phase 1 script in order: setup check -> inventory -> profiling ->
relationships.

Usage:
    python scripts/run_all.py
"""

import runpy
import sys
from pathlib import Path

import _bootstrap  # noqa: F401

from hhgoa_fraud.logging_utils import get_logger

log = get_logger("run_all")

SCRIPTS = [
    "00_check_setup.py",
    "01_inspect_dataset.py",
    "02_profile_dataset.py",
    "03_explore_relationships.py",
]


def main() -> None:
    here = Path(__file__).resolve().parent
    for name in SCRIPTS:
        log.info("=" * 70)
        log.info("Running %s", name)
        log.info("=" * 70)
        # run_path with a fresh __main__ so each script's `if __name__ == "__main__"` fires
        sys.argv = [str(here / name)]
        runpy.run_path(str(here / name), run_name="__main__")


if __name__ == "__main__":
    main()
