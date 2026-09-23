"""Sanity-check that the project is ready to run: dependencies importable,
data/ present, and at least one dataset file found. Run this first.

Usage:
    python scripts/00_check_setup.py
"""

import _bootstrap  # noqa: F401

from hhgoa_fraud.config import get_settings
from hhgoa_fraud.io_utils import discover_files
from hhgoa_fraud.logging_utils import get_logger

log = get_logger("check_setup")

REQUIRED_MODULES = ["pandas", "numpy", "dotenv", "tabulate", "pypdf"]


def main() -> None:
    log.info("Checking required packages ...")
    missing = []
    for mod in REQUIRED_MODULES:
        try:
            __import__(mod)
        except ImportError:
            missing.append(mod)
    if missing:
        log.error("Missing packages: %s -- run: pip install -r requirements.txt", ", ".join(missing))
    else:
        log.info("All required packages are importable.")

    settings = get_settings()
    log.info("DATA_DIR resolved to: %s", settings.data_dir)
    if not settings.data_dir.exists():
        log.warning("data/ does not exist yet. Creating it.")
        settings.data_dir.mkdir(parents=True, exist_ok=True)

    files = discover_files(settings.data_dir)
    if not files:
        log.warning(
            "No dataset files found under %s. "
            "Place the HHGOA dataset (CSV/README/etc.) there, then re-run this script.",
            settings.data_dir,
        )
    else:
        log.info("Found %d file(s) under %s:", len(files), settings.data_dir)
        for f in files:
            log.info("  - %s (%s, %.2f MB)", f.rel, f.kind, f.size_mb)

    settings.reports_dir.mkdir(parents=True, exist_ok=True)
    log.info("Reports will be written to: %s", settings.reports_dir)
    log.info("Setup check complete.")


if __name__ == "__main__":
    main()
