"""Step 3 - Discover relationships between files.

Two things are computed, both from the data itself:
  1. Which (normalized) column names appear in more than one file - candidate
     join keys such as an ID that shows up in transactions, identity, and
     case history files.
  2. For each candidate pair, what fraction of the values in one file's
     column actually appear in the other file's column (sampled for large
     files, and clearly labeled as sampled).

Nothing here declares a relationship ("this is a foreign key") unless the
overlap numbers support it - the report shows the raw percentages so you can
judge.

Usage:
    python scripts/03_explore_relationships.py [--sample-rows N] [--min-overlap-pct P]
"""

import argparse

import _bootstrap  # noqa: F401
import pandas as pd

from hhgoa_fraud.config import get_settings
from hhgoa_fraud.io_utils import discover_files
from hhgoa_fraud.logging_utils import get_logger
from hhgoa_fraud.relationships import DEFAULT_SAMPLE_ROWS, compute_overlap, find_shared_columns
from hhgoa_fraud.reporting import MarkdownReport, write_json

log = get_logger("explore_relationships")


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--sample-rows", type=int, default=DEFAULT_SAMPLE_ROWS)
    parser.add_argument(
        "--min-overlap-pct",
        type=float,
        default=1.0,
        help="Only report pairs where at least one side overlaps by this %% or more.",
    )
    args = parser.parse_args()

    settings = get_settings()
    files = discover_files(settings.data_dir)
    tabular = [f for f in files if f.kind == "tabular"]
    if len(tabular) < 2:
        log.warning("Need at least 2 tabular files to find relationships; found %d.", len(tabular))
        if not tabular:
            return

    by_rel = {f.rel: f for f in tabular}

    log.info("Looking for shared column names across %d file(s) ...", len(tabular))
    shared_columns = find_shared_columns(tabular)
    log.info("Found %d normalized column name(s) shared by 2+ files.", len(shared_columns))

    overlap_rows = []
    overlap_results = []
    for sc in shared_columns:
        # Compare every pair of files that has this column name.
        for i in range(len(sc.occurrences)):
            for j in range(i + 1, len(sc.occurrences)):
                (file_a_rel, col_a), (file_b_rel, col_b) = sc.occurrences[i], sc.occurrences[j]
                try:
                    result = compute_overlap(
                        by_rel[file_a_rel], col_a, by_rel[file_b_rel], col_b, sample_rows=args.sample_rows
                    )
                except Exception as exc:  # noqa: BLE001
                    log.warning("Could not compare %s.%s vs %s.%s: %s", file_a_rel, col_a, file_b_rel, col_b, exc)
                    continue
                overlap_results.append(result)
                if max(result.pct_of_a, result.pct_of_b) >= args.min_overlap_pct:
                    overlap_rows.append(
                        {
                            "column": sc.normalized_name,
                            "file_a": result.file_a,
                            "file_b": result.file_b,
                            "distinct_a": result.distinct_a,
                            "distinct_b": result.distinct_b,
                            "shared": result.shared,
                            "%_of_a_covered": result.pct_of_a,
                            "%_of_b_covered": result.pct_of_b,
                            "sampled": result.sampled,
                        }
                    )

    overlap_df = pd.DataFrame(overlap_rows).sort_values(
        by=["%_of_a_covered", "%_of_b_covered"], ascending=False
    ) if overlap_rows else pd.DataFrame()

    report = MarkdownReport("HHGOA Relationships Between Files")
    report.para(
        f"Compared columns across **{len(tabular)}** tabular file(s). "
        f"Overlap was sampled at up to {args.sample_rows:,} rows per column when files were large."
    )

    report.h2("Shared column names (candidate join keys)")
    if not shared_columns:
        report.para("_No column name appears in more than one file (by normalized name)._")
    else:
        shared_rows = [
            {
                "normalized_name": sc.normalized_name,
                "appears_in": ", ".join(f"{rel} (`{col}`)" for rel, col in sc.occurrences),
            }
            for sc in shared_columns
        ]
        report.table(pd.DataFrame(shared_rows))

    report.h2(f"Value overlap (pairs with >= {args.min_overlap_pct}% coverage on either side)")
    if overlap_df.empty:
        report.para(
            "_No pair reached the overlap threshold. Either the files don't share real keys, "
            "or try lowering --min-overlap-pct._"
        )
    else:
        report.table(overlap_df)

    report.h2("How to read this")
    report.bullets(
        [
            "`%_of_a_covered` = share of file A's distinct values that were also seen in file B (and vice versa).",
            "A high percentage on both sides (e.g. >80%) is strong evidence of a real join key between two files.",
            "A high percentage on only one side can mean one file is a subset of the other's entities "
            "(e.g. only the customers who ever had a case).",
            "`sampled: True` means the comparison used a row sample rather than the full file - "
            "treat the percentage as approximate.",
        ]
    )

    out_md = settings.reports_dir / "03_relationships.md"
    report.save(out_md)
    log.info("Wrote %s", out_md)

    write_json(
        settings.reports_dir / "03_relationships.json",
        {
            "shared_columns": shared_columns,
            "overlaps": overlap_results,
        },
    )
    log.info("Wrote %s", settings.reports_dir / "03_relationships.json")


if __name__ == "__main__":
    main()
