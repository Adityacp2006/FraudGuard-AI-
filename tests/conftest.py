"""Synthetic fixtures used to test the profiling tools without the real
(large, competition-restricted) HHGOA dataset.

The column names below are intentionally generic (customer_id, card_id,
transaction_id, amount, device_id, ...) and are placeholders for testing
join/overlap/profiling logic only - they are NOT claims about the real
HHGOA schema, which scripts/01_inspect_dataset.py discovers from the actual
dataset README.
"""

from __future__ import annotations

from pathlib import Path

import pytest

from hhgoa_fraud.io_utils import discover_files


@pytest.fixture()
def synthetic_data_dir(tmp_path: Path) -> Path:
    data_dir = tmp_path / "data"
    data_dir.mkdir()

    (data_dir / "README.md").write_text(
        "\n".join(
            [
                "# Synthetic Dataset README",
                "",
                "## Files",
                "This dataset consists of transactions.csv and closed_cases_history.csv.",
                "",
                "## Transaction fields",
                "Each row in transactions.csv is one card transaction with an amount and merchant.",
                "",
                "## Customer and account information",
                "customer_id identifies the account holder; billing_region is their region.",
                "",
                "## Device and connection information",
                "device_id and ip_address describe the connection used for the transaction.",
                "",
                "## Previous fraud cases",
                "closed_cases_history.csv contains prior resolved fraud cases.",
                "",
                "## Fraud policy",
                "Rule R1: a single weak signal with probability < 0.70 requires step-up auth.",
                "",
                "## Benchmark cases",
                "case_pack.csv contains the 20 benchmark cases HHG-001 through HHG-020.",
                "",
            ]
        ),
        encoding="utf-8",
    )

    transactions = "\n".join(
        [
            "transaction_id,customer_id,amount,device_id,region,note",
            "T1,C1,100.5,D1,IN,ok",
            "T2,C1,,D1,IN,",
            "T3,C2,45.0,D2,US,NA",
            "T4,C3,9999.99,D2,US,null",
            "T5,C2,20.0,D3,IN,ok",
        ]
    )
    (data_dir / "transactions.csv").write_text(transactions, encoding="utf-8")

    cases = "\n".join(
        [
            "case_id,customer_id,verdict",
            "CASE1,C1,cleared",
            "CASE2,C2,fraud",
        ]
    )
    (data_dir / "closed_cases_history.csv").write_text(cases, encoding="utf-8")

    case_pack = "\n".join(
        [
            "case_ref,transaction_id",
            "HHG-001,T1",
            "HHG-002,T4",
        ]
    )
    (data_dir / "case_pack.csv").write_text(case_pack, encoding="utf-8")

    return data_dir


@pytest.fixture()
def synthetic_files(synthetic_data_dir: Path):
    return discover_files(synthetic_data_dir)
