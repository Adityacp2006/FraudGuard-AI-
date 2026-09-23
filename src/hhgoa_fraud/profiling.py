"""Column- and table-level profiling.

Everything here is computed from what is actually in the file - no schema or
fraud-label assumptions are hard-coded. Large files are read in row chunks
(and, if very wide, in column batches too) so memory stays bounded regardless
of file size.
"""

from __future__ import annotations

import time
from dataclasses import dataclass, field

import numpy as np
import pandas as pd

from .config import Settings
from .io_utils import FileInfo, chunked, read_header, read_table
from .row_count import count_rows

# Tokens that often mean "missing" in the wild but are NOT auto-converted to
# NaN (see io_utils docstring) - we just flag how often they appear.
NULL_LIKE_TOKENS = {"na", "n/a", "null", "none", "nan", "-", "--", "unknown", "nil", "missing", "?"}

DEFAULT_ROW_CHUNKSIZE = 100_000
DEFAULT_UNIQUE_CAP = 200_000
DEFAULT_SAMPLE_SIZE = 5


@dataclass
class ColumnProfile:
    name: str
    dtype: str
    non_null: int
    missing: int
    missing_pct: float
    unique: int | None
    unique_is_lower_bound: bool
    sample_values: list[str]
    numeric_min: float | None = None
    numeric_max: float | None = None
    numeric_mean: float | None = None
    null_like_token_count: int = 0
    top_values: list[tuple[str, int]] = field(default_factory=list)


@dataclass
class TableProfile:
    file: str
    size_mb: float
    n_rows: int
    n_cols: int
    columns: list[ColumnProfile]
    duration_seconds: float
    warnings: list[str] = field(default_factory=list)


class _ColumnAccumulator:
    """Running statistics for one column, fed one chunk at a time."""

    def __init__(self, name: str, unique_cap: int, sample_size: int, top_n: int) -> None:
        self.name = name
        self._unique_cap = unique_cap
        self._sample_size = sample_size
        self._top_n = top_n
        self.non_null = 0
        self.missing = 0
        self._dtypes: set[str] = set()
        self._unique: set | None = set()
        self._unique_lower_bound = 0
        self._samples: list[str] = []
        self._num_count = 0
        self._num_sum = 0.0
        self._num_min: float | None = None
        self._num_max: float | None = None
        self._null_like = 0
        self._value_counts: pd.Series | None = None

    def update(self, s: pd.Series) -> None:
        self.missing += int(s.isna().sum())
        non_null = s.dropna()
        self.non_null += len(non_null)
        self._dtypes.add(str(s.dtype))

        if pd.api.types.is_numeric_dtype(s) and len(non_null):
            vals = non_null.to_numpy(dtype="float64", na_value=np.nan)
            vals = vals[~np.isnan(vals)]
            if len(vals):
                self._num_count += len(vals)
                self._num_sum += float(vals.sum())
                mn, mx = float(vals.min()), float(vals.max())
                self._num_min = mn if self._num_min is None else min(self._num_min, mn)
                self._num_max = mx if self._num_max is None else max(self._num_max, mx)

        if len(non_null):
            uniques = non_null.astype(str).unique()
            if self._unique is not None:
                self._unique.update(uniques.tolist())
                if len(self._unique) > self._unique_cap:
                    self._unique_lower_bound = len(self._unique)
                    self._unique = None  # stop tracking exactly; too costly
            else:
                self._unique_lower_bound = max(self._unique_lower_bound, len(uniques))

            for v in uniques:
                if len(self._samples) >= self._sample_size:
                    break
                if v not in self._samples:
                    self._samples.append(v)

            if not pd.api.types.is_numeric_dtype(s):
                lowered = non_null.astype(str).str.strip().str.lower()
                self._null_like += int(lowered.isin(NULL_LIKE_TOKENS).sum())
                vc = non_null.astype(str).value_counts()
                self._value_counts = vc if self._value_counts is None else self._value_counts.add(vc, fill_value=0)

    def finalize(self, total_rows: int) -> ColumnProfile:
        missing_pct = round(100.0 * self.missing / total_rows, 2) if total_rows else 0.0
        mean = round(self._num_sum / self._num_count, 4) if self._num_count else None
        dtype = self._dtypes.pop() if len(self._dtypes) == 1 else "mixed(" + ",".join(sorted(self._dtypes)) + ")"
        if self._unique is not None:
            unique, lower_bound = len(self._unique), False
        else:
            unique, lower_bound = self._unique_lower_bound, True
        top_values: list[tuple[str, int]] = []
        if self._value_counts is not None:
            top = self._value_counts.sort_values(ascending=False).head(self._top_n)
            top_values = [(str(idx), int(cnt)) for idx, cnt in top.items()]
        return ColumnProfile(
            name=self.name,
            dtype=dtype,
            non_null=self.non_null,
            missing=self.missing,
            missing_pct=missing_pct,
            unique=unique,
            unique_is_lower_bound=lower_bound,
            sample_values=self._samples,
            numeric_min=self._num_min,
            numeric_max=self._num_max,
            numeric_mean=mean,
            null_like_token_count=self._null_like,
            top_values=top_values,
        )


def _iter_row_chunks(info: FileInfo, columns: list[str], chunksize: int, engine: str):
    """Yield DataFrame chunks covering only ``columns``, for any supported format."""
    if info.suffix in {".csv", ".tsv"}:
        sep = "\t" if info.suffix == ".tsv" else ","
        reader = pd.read_csv(
            info.path,
            sep=sep,
            usecols=columns,
            chunksize=chunksize,
            keep_default_na=False,
            na_values=[""],
            low_memory=False,
        )
        yield from reader
    else:
        # Parquet / JSONL: columnar or small enough to read whole, then slice.
        df = read_table(info, columns=columns)
        for start in range(0, len(df), chunksize):
            yield df.iloc[start : start + chunksize]


def profile_table(
    info: FileInfo,
    settings: Settings,
    row_chunksize: int = DEFAULT_ROW_CHUNKSIZE,
    unique_cap: int = DEFAULT_UNIQUE_CAP,
    sample_size: int = DEFAULT_SAMPLE_SIZE,
    top_n: int = 10,
) -> TableProfile:
    """Profile one tabular file: rows, columns, missing, dtypes, uniques, top values."""
    start = time.time()
    warnings: list[str] = []
    columns = read_header(info)
    exact_rows = count_rows(info)

    accumulators = {c: _ColumnAccumulator(c, unique_cap, sample_size, top_n) for c in columns}
    rows_seen_per_batch: list[int] = []

    for batch_cols in chunked(columns, settings.column_batch_size):
        rows_in_this_batch = 0
        for chunk in _iter_row_chunks(info, batch_cols, row_chunksize, settings.csv_engine):
            rows_in_this_batch += len(chunk)
            for col in batch_cols:
                accumulators[col].update(chunk[col])
        rows_seen_per_batch.append(rows_in_this_batch)

    if rows_seen_per_batch and len(set(rows_seen_per_batch)) > 1:
        warnings.append(
            f"Row counts differed across column batches ({sorted(set(rows_seen_per_batch))}); "
            "the file may have ragged rows."
        )

    n_rows = exact_rows if exact_rows is not None else (rows_seen_per_batch[0] if rows_seen_per_batch else 0)
    if exact_rows is not None and rows_seen_per_batch and exact_rows != rows_seen_per_batch[0]:
        warnings.append(
            f"Line-count row total ({exact_rows}) differs from parsed row total ({rows_seen_per_batch[0]})."
        )

    col_profiles = [accumulators[c].finalize(n_rows) for c in columns]
    return TableProfile(
        file=info.rel,
        size_mb=round(info.size_mb, 2),
        n_rows=n_rows,
        n_cols=len(columns),
        columns=col_profiles,
        duration_seconds=round(time.time() - start, 2),
        warnings=warnings,
    )
