"""Fast, exact row counting for tabular files.

Counting rows this way (streaming bytes, no pandas) keeps memory flat even for
multi-hundred-MB CSVs, and lets every profiling report state a definitive row
count instead of an estimate.
"""

from __future__ import annotations

from .io_utils import FileInfo


def count_rows(info: FileInfo) -> int | None:
    """Exact data-row count (header excluded). Returns None if unsupported."""
    if info.suffix in {".csv", ".tsv"}:
        return _count_lines(info.path) - 1  # minus header
    if info.suffix in {".jsonl", ".ndjson"}:
        return _count_lines(info.path)
    if info.suffix == ".parquet":
        import pyarrow.parquet as pq

        return pq.ParquetFile(info.path).metadata.num_rows
    return None


def _count_lines(path) -> int:
    count = 0
    with open(path, "rb") as fh:
        buf_size = 1024 * 1024
        buf = fh.read(buf_size)
        ends_with_newline = True
        while buf:
            count += buf.count(b"\n")
            ends_with_newline = buf.endswith(b"\n")
            buf = fh.read(buf_size)
        if count and not ends_with_newline:
            count += 1  # last line has no trailing newline
    return count
