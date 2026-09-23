from hhgoa_fraud.relationships import compute_overlap, find_shared_columns


def test_find_shared_columns_detects_customer_id_and_transaction_id(synthetic_files):
    tabular = [f for f in synthetic_files if f.kind == "tabular"]
    shared = find_shared_columns(tabular)
    names = {sc.normalized_name for sc in shared}
    assert "customerid" in names
    assert "transactionid" in names

    customer_id_files = {rel for rel, _ in next(sc for sc in shared if sc.normalized_name == "customerid").occurrences}
    assert customer_id_files == {"transactions.csv", "closed_cases_history.csv"}


def test_compute_overlap_detects_full_match_on_shared_customers(synthetic_files):
    by_rel = {f.rel: f for f in synthetic_files}
    result = compute_overlap(
        by_rel["closed_cases_history.csv"], "customer_id", by_rel["transactions.csv"], "customer_id"
    )
    # Every customer_id in closed_cases_history.csv (C1, C2) also appears in transactions.csv
    assert result.pct_of_a == 100.0
    assert result.shared == 2


def test_compute_overlap_partial_match_case_pack_to_transactions(synthetic_files):
    by_rel = {f.rel: f for f in synthetic_files}
    result = compute_overlap(by_rel["case_pack.csv"], "transaction_id", by_rel["transactions.csv"], "transaction_id")
    # case_pack references T1 and T4, both of which exist in transactions.csv
    assert result.shared == 2
    assert result.pct_of_a == 100.0
    # But transactions.csv has more transaction_ids than case_pack references
    assert result.pct_of_b < 100.0
