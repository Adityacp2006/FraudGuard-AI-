"""File discovery and table reading.

Design rules:
* Nothing here knows the dataset's file names or columns - everything is
  discovered from disk.
* Only cells that are literally empty are treated as missing. Pandas' default
  NA tokens ("NA", "N/A", "null", ...) are NOT converted, because "NA" can be a
  legitimate value (e.g. a country code). Null-like tokens are counted
  separately by the profiler so they stay visible.
"""

from __future__ import annotations

import re
from collections.abc import Iterable, Sequence
from dataclasses import dataclass
from pathlib import Path

import pandas as pd

TABULAR_SUFFIXES = {".csv", ".tsv", ".parquet", ".jsonl", ".ndjson"}
DOC_SUFFIXES = {".md", ".markdown", ".txt", ".rst", ".pdf"}
_SKIP_DIR_NAMES = {"processed", "__macosx", ".git", ".ipynb_checkpoints", "__pycache__"}


@dataclass(frozen=True)
class FileInfo:
    path: Path
    rel: str  # path relative to the scanned directory, POSIX style
    size_bytes: int
    suffix: str  # effective suffix, ignoring a trailing .gz
    kind: str  # "tabular" | "document" | "other"

    @property
    def size_mb(self) -> float:
        return self.size_bytes / (1024 * 1024)


def _effective_suffix(path: Path) -> str:
    suffixes = [s.lower() for s in path.suffixes]
    if suffixes and suffixes[-1] == ".gz":
        suffixes = suffixes[:-1]
    return suffixes[-1] if suffixes else ""


def discover_files(data_dir: Path) -> list[FileInfo]:
    """Recursively list every file under ``data_dir`` (skipping processed/hidden)."""
    if not data_dir.exists():
        return []
    found: list[FileInfo] = []
    for path in sorted(data_dir.rglob("*")):
        if not path.is_file():
            continue
        rel_parts = path.relative_to(data_dir).parts
        if any(part.lower() in _SKIP_DIR_NAMES for part in rel_parts[:-1]):
            continue
        if path.name.startswith("."):
            continue
        suffix = _effective_suffix(path)
        if suffix in TABULAR_SUFFIXES:
            kind = "tabular"
        elif suffix in DOC_SUFFIXES:
            kind = "document"
        else:
            kind = "other"
        found.append(
            FileInfo(
                path=path,
                rel=path.relative_to(data_dir).as_posix(),
                size_bytes=path.stat().st_size,
                suffix=suffix,
                kind=kind,
            )
        )
    return found


def normalize_name(name: str) -> str:
    """Lower-case and strip separators: ``Card_ID`` and ``cardId`` -> ``cardid``."""
    return re.sub(r"[^a-z0-9]", "", str(name).lower())


def chunked(items: Sequence, size: int) -> Iterable[list]:
    for i in range(0, len(items), size):
        yield list(items[i : i + size])


def _csv_kwargs(info: FileInfo, columns, nrows, as_str: bool, engine: str) -> dict:
    kw: dict = dict(
        sep="\t" if info.suffix == ".tsv" else ",",
        usecols=list(columns) if columns is not None else None,
        nrows=nrows,
        keep_default_na=False,
        na_values=[""],
    )
    if engine == "pyarrow":
        kw["engine"] = "pyarrow"
        # pyarrow engine has no nrows support in some versions; caller slices.
        kw.pop("nrows")
    else:
        kw["low_memory"] = False
    if as_str:
        kw["dtype"] = str
    return kw


def read_header(info: FileInfo) -> list[str]:
    """Column names of a tabular file without loading its rows."""
    if info.suffix in {".csv", ".tsv"}:
        return list(pd.read_csv(info.path, nrows=0, sep="\t" if info.suffix == ".tsv" else ",").columns)
    if info.suffix == ".parquet":
        import pyarrow.parquet as pq

        return list(pq.ParquetFile(info.path).schema.names)
    if info.suffix in {".jsonl", ".ndjson"}:
        return list(pd.read_json(info.path, lines=True, nrows=1000).columns)
    raise ValueError(f"Unsupported tabular format: {info.suffix}")


def read_table(
    info: FileInfo,
    columns: Sequence[str] | None = None,
    nrows: int | None = None,
    as_str: bool = False,
    engine: str = "c",
) -> pd.DataFrame:
    """Read (a subset of) a tabular file. ``as_str=True`` keeps raw text values."""
    if info.suffix in {".csv", ".tsv"}:
        if engine == "pyarrow":
            try:
                df = pd.read_csv(info.path, **_csv_kwargs(info, columns, nrows, as_str, "pyarrow"))
                return df.head(nrows) if nrows is not None else df
            except Exception:  # fall back to the predictable C engine
                pass
        return pd.read_csv(info.path, **_csv_kwargs(info, columns, nrows, as_str, "c"))
    if info.suffix == ".parquet":
        df = pd.read_parquet(info.path, columns=list(columns) if columns is not None else None)
    elif info.suffix in {".jsonl", ".ndjson"}:
        df = pd.read_json(info.path, lines=True, nrows=nrows)
        if columns is not None:
            df = df[list(columns)]
    else:
        raise ValueError(f"Unsupported tabular format: {info.suffix}")
    if nrows is not None:
        df = df.head(nrows)
    return df.astype("string") if as_str else df


_FLOATY_INT = r"^(-?\d+)\.0+$"


def normalize_key_series(s: pd.Series) -> pd.Series:
    """Clean a column for key comparison across files.

    Drops missing/blank values, trims whitespace, and turns "123.0" into "123"
    (a common artefact of integer columns that contained NaN when exported).
    """
    s = s.dropna().astype(str).str.strip()
    s = s[s != ""]
    return s.str.replace(_FLOATY_INT, r"\1", regex=True)
