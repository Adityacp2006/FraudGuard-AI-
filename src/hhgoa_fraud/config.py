"""Central configuration.

All settings come from environment variables (optionally loaded from a local
``.env`` file) with safe defaults, so every script behaves the same whether it
is run from the terminal, the VS Code debugger, or a test.
"""

from __future__ import annotations

import os
from dataclasses import dataclass
from pathlib import Path

from dotenv import load_dotenv

PROJECT_ROOT = Path(__file__).resolve().parents[2]
load_dotenv(PROJECT_ROOT / ".env")


def _resolve_path(env_name: str, default: str) -> Path:
    raw = os.getenv(env_name) or default
    path = Path(raw).expanduser()
    return path if path.is_absolute() else (PROJECT_ROOT / path).resolve()


def _int_env(env_name: str, default: int) -> int:
    raw = os.getenv(env_name)
    if raw in (None, ""):
        return default
    try:
        return int(raw)
    except ValueError:
        return default


@dataclass(frozen=True)
class Settings:
    project_root: Path
    data_dir: Path
    processed_dir: Path
    reports_dir: Path
    log_level: str
    # Files larger than this are profiled in column batches instead of one pass.
    large_file_mb: int
    # Number of columns read per pass for large files.
    column_batch_size: int
    # A column with at most this many distinct values is flagged "low cardinality".
    low_cardinality_max: int
    # "c" (default, most predictable) or "pyarrow" (faster on big files).
    csv_engine: str


def get_settings() -> Settings:
    data_dir = _resolve_path("DATA_DIR", "data")
    return Settings(
        project_root=PROJECT_ROOT,
        data_dir=data_dir,
        processed_dir=data_dir / "processed",
        reports_dir=_resolve_path("REPORTS_DIR", "reports"),
        log_level=os.getenv("LOG_LEVEL", "INFO").upper(),
        large_file_mb=_int_env("LARGE_FILE_MB", 150),
        column_batch_size=max(1, _int_env("COLUMN_BATCH_SIZE", 60)),
        low_cardinality_max=max(2, _int_env("LOW_CARDINALITY_MAX", 25)),
        csv_engine=os.getenv("CSV_ENGINE", "c").lower(),
    )
