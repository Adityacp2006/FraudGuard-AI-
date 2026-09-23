import pandas as pd

from hhgoa_fraud.io_utils import chunked, normalize_key_series, normalize_name, read_header, read_table


def test_discover_files_classifies_kinds(synthetic_files):
    kinds = {f.rel: f.kind for f in synthetic_files}
    assert kinds["transactions.csv"] == "tabular"
    assert kinds["README.md"] == "document"


def test_normalize_name_matches_across_styles():
    assert normalize_name("Customer_ID") == normalize_name("customerId") == normalize_name("CUSTOMER-ID")


def test_chunked_splits_evenly_and_with_remainder():
    assert list(chunked([1, 2, 3, 4, 5], 2)) == [[1, 2], [3, 4], [5]]


def test_read_header_returns_columns(synthetic_files):
    info = next(f for f in synthetic_files if f.rel == "transactions.csv")
    assert read_header(info) == ["transaction_id", "customer_id", "amount", "device_id", "region", "note"]


def test_read_table_keeps_blank_as_na_but_not_text_na(synthetic_files):
    info = next(f for f in synthetic_files if f.rel == "transactions.csv")
    df = read_table(info)
    # Truly blank cell -> NaN
    assert pd.isna(df.loc[df["transaction_id"] == "T2", "note"].iloc[0])
    # Literal text "NA" is NOT converted to NaN (it's a real value to inspect)
    assert df.loc[df["transaction_id"] == "T3", "note"].iloc[0] == "NA"


def test_normalize_key_series_strips_float_suffix():
    s = pd.Series(["123.0", " 45 ", "", None, "67.00"])
    cleaned = normalize_key_series(s)
    assert list(cleaned) == ["123", "45", "67"]
