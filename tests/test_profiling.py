from hhgoa_fraud.config import get_settings
from hhgoa_fraud.profiling import profile_table
from hhgoa_fraud.row_count import count_rows


def _col(profile, name):
    return next(c for c in profile.columns if c.name == name)


def test_count_rows_matches_data_rows(synthetic_files):
    info = next(f for f in synthetic_files if f.rel == "transactions.csv")
    assert count_rows(info) == 5  # header excluded


def test_profile_table_basic_shape(synthetic_data_dir, synthetic_files, monkeypatch):
    monkeypatch.setenv("DATA_DIR", str(synthetic_data_dir))
    settings = get_settings()
    info = next(f for f in synthetic_files if f.rel == "transactions.csv")

    profile = profile_table(info, settings, row_chunksize=2)  # force multiple chunks
    assert profile.n_rows == 5
    assert profile.n_cols == 6


def test_profile_table_missing_and_dtype(synthetic_data_dir, synthetic_files, monkeypatch):
    monkeypatch.setenv("DATA_DIR", str(synthetic_data_dir))
    settings = get_settings()
    info = next(f for f in synthetic_files if f.rel == "transactions.csv")
    profile = profile_table(info, settings, row_chunksize=2)

    amount = _col(profile, "amount")
    assert amount.missing == 1  # the blank cell for T2
    assert amount.non_null == 4
    assert amount.numeric_min == 20.0
    assert amount.numeric_max == 9999.99

    customer_id = _col(profile, "customer_id")
    assert customer_id.unique == 3  # C1, C2, C3
    assert set(customer_id.sample_values) <= {"C1", "C2", "C3"}


def test_profile_table_flags_null_like_tokens_without_converting_them(
    synthetic_data_dir, synthetic_files, monkeypatch
):
    monkeypatch.setenv("DATA_DIR", str(synthetic_data_dir))
    settings = get_settings()
    info = next(f for f in synthetic_files if f.rel == "transactions.csv")
    profile = profile_table(info, settings, row_chunksize=2)

    note = _col(profile, "note")
    # "NA" and "null" are literal text values, present -> counted as null-like
    # but NOT counted as `missing` (only the truly blank cell is).
    assert note.null_like_token_count == 2
    assert note.missing == 1
