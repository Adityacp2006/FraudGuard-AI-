python -c "from dotenv import load_dotenv; import os; import pyTigerGraph as tg; load_dotenv(); conn=tg.TigerGraphConnection(host=os.getenv('TG_HOST'), graphname=os.getenv('TG_GRAPH'), apiToken=os.getenv('TG_TOKEN')); print('CONNECTED'); print(conn.getSchema())""""Step 2 - Profile every tabular file in data/.

For each file, computes (with no assumptions about column meaning):
  - number of rows, number of columns
  - per-column: dtype, missing count/%, unique count, sample values,
    numeric min/max/mean where applicable, top values for categorical columns
  - a flag for common "null-like" text tokens (e.g. "NA", "null") that were
    NOT auto-converted to missing, so they stay visible for manual review

Large files are read in bounded-memory chunks, so this is safe to run on the
full ~700MB transaction file.

Writes one reports/profile_<file>.md/.json per file, plus a combined
reports/02_profiling_summary.md.

Usage:
    python scripts/02_profile_dataset.py [--sample-rows N] [--file NAME]
"""

import argparse
import time

import _bootstrap  # noqa: F401
import pandas as pd

from hhgoa_fraud.config import get_settings
from hhgoa_fraud.io_utils import discover_files
from hhgoa_fraud.logging_utils import get_logger
from hhgoa_fraud.profiling import TableProfile, profile_table
from hhgoa_fraud.reporting import MarkdownReport, write_json

log = get_logger("profile_dataset")


def _safe_filename(rel_path: str) -> str:
    return rel_path.replace("/", "__").replace("\\", "__")


def _columns_dataframe(profile: TableProfile) -> pd.DataFrame:
    rows = []
    for c in profile.columns:
        rows.append(
            {
                "column": c.name,
                "dtype": c.dtype,
                "missing": c.missing,
                "missing_%": c.missing_pct,
                "unique": f"{c.unique}{'+' if c.unique_is_lower_bound else ''}",
                "min": c.numeric_min,
                "max": c.numeric_max,
                "mean": c.numeric_mean,
                "null_like_tokens": c.null_like_token_count,
                "sample_values": ", ".join(map(str, c.sample_values)),
            }
        )
    return pd.DataFrame(rows)


def write_file_report(profile: TableProfile, settings) -> None:
    report = MarkdownReport(f"Profile: {profile.file}")
    report.bullets(
        [
            f"Size on disk: {profile.size_mb} MB",
            f"Rows: {profile.n_rows:,}",
            f"Columns: {profile.n_cols}",
            f"Profiling time: {profile.duration_seconds}s",
        ]
    )
    if profile.warnings:
        report.h2("Warnings")
        report.bullets(profile.warnings)

    report.h2("Columns")
    report.table(_columns_dataframe(profile))

    report.h2("Top values for categorical columns (max 10 each)")
    any_top = False
    for c in profile.columns:
        if c.top_values:
            any_top = True
            report.h3(c.name)
            top_df = pd.DataFrame(c.top_values, columns=["value", "count"])
            report.table(top_df)
    if not any_top:
        report.para("_No categorical columns with tracked top values (all numeric, or all high-cardinality)._")

    out_md = settings.reports_dir / f"profile_{_safe_filename(profile.file)}.md"
    report.save(out_md)
    write_json(settings.reports_dir / f"profile_{_safe_filename(profile.file)}.json", profile)
    log.info("  wrote %s", out_md)


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--file", help="Only profile this one file (relative path under data/).")
    args = parser.parse_args()

    settings = get_settings()
    files = [f for f in discover_files(settings.data_dir) if f.kind == "tabular"]
    if args.file:
        files = [f for f in files if f.rel == args.file]
        if not files:
            log.error("No tabular file matching %s found under %s.", args.file, settings.data_dir)
            return
    if not files:
        log.error("No tabular files found under %s. Run scripts/00_check_setup.py for guidance.", settings.data_dir)
        return

    summary_rows = []
    all_profiles: list[TableProfile] = []

    for info in files:
        log.info("Profiling %s (%.2f MB) ...", info.rel, info.size_mb)
        t0 = time.time()
        profile = profile_table(info, settings)
        log.info("  done in %.1fs -> %s rows x %s cols", time.time() - t0, f"{profile.n_rows:,}", profile.n_cols)
        write_file_report(profile, settings)
        all_profiles.append(profile)

        total_missing = sum(c.missing for c in profile.columns)
        total_cells = profile.n_rows * profile.n_cols
        summary_rows.append(
            {
                "file": profile.file,
                "size_mb": profile.size_mb,
                "rows": profile.n_rows,
                "columns": profile.n_cols,
                "missing_cells": total_missing,
                "missing_%_overall": round(100 * total_missing / total_cells, 2) if total_cells else 0,
                "warnings": len(profile.warnings),
            }
        )

    summary_df = pd.DataFrame(summary_rows)
    report = MarkdownReport("HHGOA Dataset Profiling Summary")
    report.para(f"Profiled **{len(files)}** tabular file(s) under `{settings.data_dir}`.")
    report.table(summary_df)
    report.h2("Per-file reports")
    report.bullets([f"`reports/profile_{_safe_filename(p.file)}.md`" for p in all_profiles])
    out_md = settings.reports_dir / "02_profiling_summary.md"
    report.save(out_md)
    write_json(settings.reports_dir / "02_profiling_summary.json", summary_rows)
    log.info("Wrote %s", out_md)


if __name__ == "__main__":
    main()
