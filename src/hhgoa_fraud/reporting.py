"""Small helpers to write Markdown and JSON reports."""

from __future__ import annotations

import json
import math
from dataclasses import asdict, is_dataclass
from datetime import date, datetime
from pathlib import Path
from typing import Any

import numpy as np
import pandas as pd


def _escape_cell(value: Any) -> str:
    if value is None or (isinstance(value, float) and math.isnan(value)):
        return ""
    text = str(value)
    return text.replace("|", "\\|").replace("\r", " ").replace("\n", "<br>")


def sanitize(obj: Any) -> Any:
    """Recursively convert to JSON-safe Python types (NaN/inf -> None)."""
    if is_dataclass(obj) and not isinstance(obj, type):
        return sanitize(asdict(obj))
    if isinstance(obj, dict):
        return {str(k): sanitize(v) for k, v in obj.items()}
    if isinstance(obj, (list, tuple, set)):
        return [sanitize(v) for v in obj]
    if isinstance(obj, np.integer):
        return int(obj)
    if isinstance(obj, (np.floating, float)):
        f = float(obj)
        return None if math.isnan(f) or math.isinf(f) else f
    if isinstance(obj, np.bool_):
        return bool(obj)
    if isinstance(obj, (pd.Timestamp, datetime, date)):
        return obj.isoformat()
    if isinstance(obj, Path):
        return obj.as_posix()
    if obj is pd.NA or obj is pd.NaT:
        return None
    return obj


def write_json(path: Path, obj: Any) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(sanitize(obj), indent=2, ensure_ascii=False), encoding="utf-8")


def df_to_markdown(df: pd.DataFrame, max_rows: int | None = None) -> str:
    """Render a DataFrame as a GitHub-flavoured Markdown table."""
    if df.empty:
        return "_(none)_"
    shown = df.head(max_rows) if max_rows else df
    shown = shown.astype(object).map(_escape_cell)
    text = shown.to_markdown(index=False)
    if max_rows and len(df) > max_rows:
        text += f"\n\n_…{len(df) - max_rows} more rows not shown._"
    return text


class MarkdownReport:
    """Accumulates Markdown and writes it to disk."""

    def __init__(self, title: str) -> None:
        self._lines: list[str] = [f"# {title}", ""]

    def h2(self, text: str) -> None:
        self._lines += [f"## {text}", ""]

    def h3(self, text: str) -> None:
        self._lines += [f"### {text}", ""]

    def para(self, text: str) -> None:
        self._lines += [text, ""]

    def bullets(self, items: list[str]) -> None:
        self._lines += [f"- {item}" for item in items] + [""]

    def table(self, df: pd.DataFrame, max_rows: int | None = None) -> None:
        self._lines += [df_to_markdown(df, max_rows), ""]

    def quote(self, text: str) -> None:
        self._lines += [f"> {line}" if line.strip() else ">" for line in text.splitlines()] + [""]

    def code(self, text: str, lang: str = "") -> None:
        self._lines += [f"```{lang}", text, "```", ""]

    def render(self) -> str:
        return "\n".join(self._lines).rstrip() + "\n"

    def save(self, path: Path) -> Path:
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(self.render(), encoding="utf-8")
        return path
