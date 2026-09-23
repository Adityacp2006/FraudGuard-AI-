from hhgoa_fraud.readme_scan import find_readme_files, scan_readme, split_into_sections


def test_find_readme_files_locates_readme(synthetic_data_dir):
    found = find_readme_files(synthetic_data_dir)
    assert any(f.rel == "README.md" for f in found)


def test_split_into_sections_finds_headings():
    text = "# Title\n\n## Files\nsome text\n\n## Transaction fields\nother text\n"
    sections = split_into_sections(text)
    headings = [s.heading for s in sections]
    assert "Files" in headings
    assert "Transaction fields" in headings


def test_scan_readme_matches_all_synthetic_categories(synthetic_data_dir):
    result = scan_readme(synthetic_data_dir)
    assert result.path == "README.md"
    matched = {m.category for m in result.matches}
    # The synthetic README was written to cover every required category.
    assert matched == {
        "files",
        "transaction_fields",
        "customer_account",
        "device_connection",
        "previous_fraud_cases",
        "fraud_policy",
        "benchmark_cases",
    }
    assert result.unmatched_categories == []


def test_scan_readme_handles_missing_readme(tmp_path):
    empty_dir = tmp_path / "empty"
    empty_dir.mkdir()
    result = scan_readme(empty_dir)
    assert result.path is None
    assert result.matches == []
    assert len(result.unmatched_categories) > 0
