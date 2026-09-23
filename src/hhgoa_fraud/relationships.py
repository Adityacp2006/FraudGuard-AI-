"""Discover how files relate to each other, purely from evidence on disk.

Two signals, both computed - never assumed:
1. Column name overlap: which normalized column names appear in more than one file.
2. Value overlap: for a candidate shared key, what fraction of each file's
   values actually appear in the other file.

No entity relationship (e.g. "this is the fraud label", "this joins to that")
is declared unless the data backs it up.
"""

from __future__ import annotations

from collections import defaultdict
from dataclasses import dataclass

from .io_utils import FileInfo, normalize_key_series, normalize_name, read_header, read_table

DEFAULT_SAMPLE_ROWS = 300_000


@dataclass
class SharedColumn:
    normalized_name: str
    occurrences: list[tuple[str, str]]  # (file_rel, original_column_name)


@dataclass
class OverlapResult:
    file_a: str
    col_a: str
    file_b: str
    col_b: str
    distinct_a: int
    distinct_b: int
    shared: int
    pct_of_a: float
    pct_of_b: float
    sampled: bool


def find_shared_columns(files: list[FileInfo]) -> list[SharedColumn]:
    """Normalized column names that appear in 2+ tabular files."""
    mapping: dict[str, list[tuple[str, str]]] = defaultdict(list)
    for info in files:
        if info.kind != "tabular":
            continue
        try:
            cols = read_header(info)
        except Exception:
            continue
        for c in cols:
            mapping[normalize_name(c)].append((info.rel, c))

    shared = [
        SharedColumn(normalized_name=key, occurrences=occ)
        for key, occ in mapping.items()
        if len({file_rel for file_rel, _ in occ}) > 1
    ]
    shared.sort(key=lambda sc: -len(sc.occurrences))
    return shared


def compute_overlap(
    file_a: FileInfo,
    col_a: str,
    file_b: FileInfo,
    col_b: str,
    sample_rows: int = DEFAULT_SAMPLE_ROWS,
) -> OverlapResult:
    """Value overlap between two columns, sampling large files for speed."""
    sa_raw = read_table(file_a, columns=[col_a], nrows=sample_rows, as_str=True)[col_a]
    sb_raw = read_table(file_b, columns=[col_b], nrows=sample_rows, as_str=True)[col_b]
    set_a = set(normalize_key_series(sa_raw).tolist())
    set_b = set(normalize_key_series(sb_raw).tolist())
    shared = set_a & set_b
    sampled = len(sa_raw) == sample_rows or len(sb_raw) == sample_rows

    return OverlapResult(
        file_a=file_a.rel,
        col_a=col_a,
        file_b=file_b.rel,
        col_b=col_b,
        distinct_a=len(set_a),
        distinct_b=len(set_b),
        shared=len(shared),
        pct_of_a=round(100.0 * len(shared) / len(set_a), 1) if set_a else 0.0,
        pct_of_b=round(100.0 * len(shared) / len(set_b), 1) if set_b else 0.0,
        sampled=sampled,
    )
