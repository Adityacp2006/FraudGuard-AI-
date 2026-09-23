"""Step 1 - Inventory the dataset and read its README first.

What this does:
  1. Lists every file under data/ (tabular + documents), with size and a
     tabular/document/other classification.
  2. Finds the dataset's own README/data-dictionary/policy document(s).
  3. Splits that document into sections and points each of the following
     categories at the section(s) that mention it, using keyword matching:
       files, transaction fields, customer/account info, device/connection
       info, previous fraud cases, fraud policy, the 20 benchmark cases.
  4. Writes reports/01_dataset_inventory.md and .json.

This script does NOT infer column meanings or fraud labels that the README
does not state - it only locates and quotes the relevant text so a human can
verify it.

Usage:
    python scripts/01_inspect_dataset.py
"""

import _bootstrap  # noqa: F401
import pandas as pd

from hhgoa_fraud.config import get_settings
from hhgoa_fraud.io_utils import discover_files, read_header
from hhgoa_fraud.logging_utils import get_logger
from hhgoa_fraud.readme_scan import CATEGORY_KEYWORDS, scan_readme
from hhgoa_fraud.reporting import MarkdownReport, write_json

log = get_logger("inspect_dataset")

CATEGORY_LABELS = {
    "files": "All files",
    "transaction_fields": "Transaction fields",
    "customer_account": "Customer / account information",
    "device_connection": "Device / connection information",
    "previous_fraud_cases": "Previous fraud cases",
    "fraud_policy": "Fraud policy",
    "benchmark_cases": "The 20 benchmark cases",
}


def main() -> None:
    settings = get_settings()
    files = discover_files(settings.data_dir)

    if not files:
        log.error("No files found under %s. Run scripts/00_check_setup.py for guidance.", settings.data_dir)
        return

    tabular = [f for f in files if f.kind == "tabular"]
    documents = [f for f in files if f.kind == "document"]
    other = [f for f in files if f.kind == "other"]
    log.info("%d tabular, %d document, %d other file(s).", len(tabular), len(documents), len(other))

    inventory_rows = []
    for f in files:
        n_cols = None
        if f.kind == "tabular":
            try:
                n_cols = len(read_header(f))
            except Exception as exc:  # noqa: BLE001
                log.warning("Could not read header of %s: %s", f.rel, exc)
        inventory_rows.append(
            {"file": f.rel, "kind": f.kind, "size_mb": round(f.size_mb, 2), "columns": n_cols}
        )
    inventory_df = pd.DataFrame(inventory_rows)

    log.info("Scanning README / data-dictionary documents ...")
    readme_result = scan_readme(settings.data_dir)
    if readme_result.path is None:
        log.warning(
            "No README/data-dictionary file found under %s "
            "(looked for names containing: readme, data_dictionary, policy, data_card).",
            settings.data_dir,
        )
    else:
        log.info("Using %s as the dataset README (%d section(s)).", readme_result.path, len(readme_result.sections))

    # ---- Markdown report -------------------------------------------------
    report = MarkdownReport("HHGOA Dataset Inventory")
    report.para(f"Scanned `{settings.data_dir}` and found **{len(files)}** file(s).")

    report.h2("1. All files")
    report.table(inventory_df)

    report.h2("2. README / data-dictionary used")
    if readme_result.path is None:
        report.para(
            "**No README-like file was found.** Add the dataset's README (any file whose name "
            "contains `readme`, `data_dictionary`, `policy`, or `data_card`) to `data/` and re-run this script."
        )
    else:
        report.para(f"Source document: `{readme_result.path}`")

        report.h2("3. Required categories located in the README")
        by_category: dict[str, list] = {c: [] for c in CATEGORY_KEYWORDS}
        for m in readme_result.matches:
            by_category[m.category].append(m)

        for category, label in CATEGORY_LABELS.items():
            report.h3(label)
            hits = by_category.get(category, [])
            if not hits:
                report.para("_Not explicitly found in the README by keyword search — check manually._")
                continue
            for m in hits[:5]:
                report.para(f"**Section: \"{m.heading}\"** (line {m.line_start + 1})")
                report.quote(m.snippet)
            if len(hits) > 5:
                report.para(f"_…and {len(hits) - 5} more matching section(s) in the README._")

        if readme_result.unmatched_categories:
            report.h2("4. Categories not found by keyword search")
            report.bullets([CATEGORY_LABELS[c] for c in readme_result.unmatched_categories])
            report.para(
                "These may still exist in the README under different wording, or may not be documented. "
                "Open the README directly to confirm before assuming they are absent."
            )

    report.h2("Notes")
    report.bullets(
        [
            "This report only *locates* text; it does not invent column meanings or fraud labels.",
            "Run `scripts/02_profile_dataset.py` next for row/column/missing-value statistics per file.",
            "Run `scripts/03_explore_relationships.py` to see how the files actually join to each other.",
        ]
    )

    out_md = settings.reports_dir / "01_dataset_inventory.md"
    report.save(out_md)
    log.info("Wrote %s", out_md)

    out_json = settings.reports_dir / "01_dataset_inventory.json"
    write_json(
        out_json,
        {
            "data_dir": settings.data_dir.as_posix(),
            "files": inventory_rows,
            "readme_path": readme_result.path,
            "readme_matches": readme_result.matches,
            "readme_unmatched_categories": readme_result.unmatched_categories,
        },
    )
    log.info("Wrote %s", out_json)


if __name__ == "__main__":
    main()
