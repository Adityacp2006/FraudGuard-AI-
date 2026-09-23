"""Tests for src/data/validate_joins.py.

Uses small in-memory/synthetic fixtures with the *real* HHGOA column names
(TransactionID, customer_id, card1, DeviceInfo, flagged_txn_id, ...) so the
join logic itself is verified without ever loading the real ~708 MB
transactions.csv. Row counts here are illustrative, not claims about the
real dataset (those live in reports/join_validation.md).
"""

from __future__ import annotations

import pandas as pd
import pytest

from data.validate_joins import (
    check_benchmark_customer_ids_exist,
    check_benchmark_txn_ids_exist,
    check_closed_case_customer_ids_exist,
    check_customer_card_one_to_one,
    check_device_sharing,
    check_identity_coverage,
    run_validation,
)


@pytest.fixture()
def transactions_df() -> pd.DataFrame:
    # 6 transactions, 3 customers, one-to-one customer_id <-> card1.
    return pd.DataFrame(
        {
            "TransactionID": ["T1", "T2", "T3", "T4", "T5", "T6"],
            "customer_id": ["C001", "C001", "C002", "C002", "C003", "C003"],
            "card1": ["1001", "1001", "1002", "1002", "1003", "1003"],
        }
    )


@pytest.fixture()
def identity_df() -> pd.DataFrame:
    # Only online transactions (T1, T3, T4, T5) have identity records.
    # DeviceInfo "PHONE-A" is shared by two different customers (C001, C002)
    # -> an investigation signal, not a claim about fraud.
    return pd.DataFrame(
        {
            "TransactionID": ["T1", "T3", "T4", "T5"],
            "DeviceInfo": ["PHONE-A", "PHONE-A", "PHONE-B", "PHONE-C"],
        }
    )


@pytest.fixture()
def case_pack_df() -> pd.DataFrame:
    return pd.DataFrame(
        {
            "case_id": ["HHG-001", "HHG-002"],
            "flagged_txn_id": ["T1", "T4"],
            "customer_id": ["C001", "C002"],
        }
    )


@pytest.fixture()
def closed_cases_df() -> pd.DataFrame:
    return pd.DataFrame(
        {
            "case_id": ["CC-0001", "CC-0002"],
            "customer_id": ["C001", "C003"],
        }
    )


# --------------------------------------------------------------------------
# Benchmark / closed-case join checks
# --------------------------------------------------------------------------


def test_benchmark_txn_ids_all_found(case_pack_df, transactions_df):
    result = check_benchmark_txn_ids_exist(case_pack_df, transactions_df)
    assert result.passed
    assert "2/2" in result.detail


def test_benchmark_txn_ids_reports_missing(case_pack_df, transactions_df):
    bad_case_pack = case_pack_df.copy()
    bad_case_pack.loc[1, "flagged_txn_id"] = "T999"  # does not exist
    result = check_benchmark_txn_ids_exist(bad_case_pack, transactions_df)
    assert not result.passed
    assert result.metric == 1
    assert "T999" in result.detail


def test_benchmark_customer_ids_all_found(case_pack_df, transactions_df):
    result = check_benchmark_customer_ids_exist(case_pack_df, transactions_df)
    assert result.passed


def test_benchmark_customer_ids_reports_missing(case_pack_df, transactions_df):
    bad_case_pack = case_pack_df.copy()
    bad_case_pack.loc[0, "customer_id"] = "C999"
    result = check_benchmark_customer_ids_exist(bad_case_pack, transactions_df)
    assert not result.passed
    assert result.metric == 1


def test_closed_case_customer_ids_all_found(closed_cases_df, transactions_df):
    result = check_closed_case_customer_ids_exist(closed_cases_df, transactions_df)
    assert result.passed


def test_closed_case_customer_ids_reports_missing(closed_cases_df, transactions_df):
    bad_closed = closed_cases_df.copy()
    bad_closed.loc[1, "customer_id"] = "C999"
    result = check_closed_case_customer_ids_exist(bad_closed, transactions_df)
    assert not result.passed
    assert "C999" in result.detail


# --------------------------------------------------------------------------
# Identity coverage (informational, never "fails")
# --------------------------------------------------------------------------


def test_identity_coverage_is_partial_and_informational(transactions_df, identity_df):
    result = check_identity_coverage(transactions_df, identity_df)
    assert result.informational
    assert result.passed  # informational checks never fail the run
    assert result.metric == 4  # T1, T3, T4, T5 out of 6 transactions
    assert "4/6" in result.detail


def test_identity_coverage_handles_empty_identity(transactions_df):
    empty_identity = pd.DataFrame({"TransactionID": [], "DeviceInfo": []})
    result = check_identity_coverage(transactions_df, empty_identity)
    assert result.metric == 0


# --------------------------------------------------------------------------
# customer_id <-> card1 one-to-one invariant
# --------------------------------------------------------------------------


def test_customer_card_one_to_one_passes_on_clean_data(transactions_df):
    result = check_customer_card_one_to_one(transactions_df)
    assert result.passed
    assert result.metric == 3  # 3 unique customers


def test_customer_card_one_to_one_detects_shared_card(transactions_df):
    # C003's transactions now (incorrectly) use C002's card1 value -> violation.
    broken = transactions_df.copy()
    broken.loc[broken["customer_id"] == "C003", "card1"] = "1002"
    result = check_customer_card_one_to_one(broken)
    assert not result.passed
    assert "NOT one-to-one" in result.detail


def test_customer_card_one_to_one_detects_customer_with_two_cards(transactions_df):
    # C001 now shows two distinct card1 values -> violation.
    broken = transactions_df.copy()
    broken.loc[1, "card1"] = "9999"
    result = check_customer_card_one_to_one(broken)
    assert not result.passed


# --------------------------------------------------------------------------
# DeviceInfo shared-customer counts (informational)
# --------------------------------------------------------------------------


def test_device_sharing_detects_shared_device(transactions_df, identity_df):
    result = check_device_sharing(transactions_df, identity_df)
    assert result.informational
    assert result.metric == 1  # only PHONE-A is shared, by C001 and C002
    assert "3 unique DeviceInfo" in result.detail
    assert "max customers on one DeviceInfo value: 2" in result.detail


def test_device_sharing_zero_when_no_devices_shared(transactions_df):
    identity_no_overlap = pd.DataFrame(
        {
            "TransactionID": ["T1", "T3", "T4"],
            "DeviceInfo": ["PHONE-A", "PHONE-B", "PHONE-C"],
        }
    )
    result = check_device_sharing(transactions_df, identity_no_overlap)
    assert result.metric == 0


# --------------------------------------------------------------------------
# End-to-end orchestration against small CSV fixtures on disk
# --------------------------------------------------------------------------


@pytest.fixture()
def small_data_dir(tmp_path, transactions_df, identity_df, case_pack_df, closed_cases_df):
    transactions_df.to_csv(tmp_path / "transactions.csv", index=False)
    identity_df.to_csv(tmp_path / "identity.csv", index=False)
    case_pack_df.to_csv(tmp_path / "case_pack.csv", index=False)
    closed_cases_df.to_csv(tmp_path / "closed_cases_history.csv", index=False)
    return tmp_path


def test_run_validation_end_to_end_all_pass(small_data_dir):
    report = run_validation(small_data_dir)
    assert report.hard_failures == []
    names = {r.name for r in report.results}
    assert "benchmark_flagged_txn_id -> TransactionID" in names
    assert "customer_id <-> card1 uniqueness" in names


def test_run_validation_missing_file_raises(tmp_path):
    with pytest.raises(FileNotFoundError):
        run_validation(tmp_path)
