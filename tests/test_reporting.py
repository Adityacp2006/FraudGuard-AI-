import json
import math
from dataclasses import dataclass

import pandas as pd

from hhgoa_fraud.reporting import MarkdownReport, df_to_markdown, sanitize, write_json


@dataclass
class _Dummy:
    a: int
    b: float


def test_sanitize_converts_nan_and_dataclasses():
    out = sanitize({"x": float("nan"), "y": _Dummy(a=1, b=2.5), "z": [1, 2, float("inf")]})
    assert out["x"] is None
    assert out["y"] == {"a": 1, "b": 2.5}
    assert out["z"] == [1, 2, None]


def test_write_json_roundtrip(tmp_path):
    path = tmp_path / "out.json"
    write_json(path, {"n": math.nan, "ok": 1})
    loaded = json.loads(path.read_text())
    assert loaded["n"] is None
    assert loaded["ok"] == 1


def test_df_to_markdown_handles_empty_and_pipes():
    assert df_to_markdown(pd.DataFrame()) == "_(none)_"
    df = pd.DataFrame({"a": ["x|y"], "b": [1]})
    md = df_to_markdown(df)
    assert "x\\|y" in md


def test_markdown_report_save(tmp_path):
    report = MarkdownReport("Title")
    report.h2("Section")
    report.para("hello")
    out = report.save(tmp_path / "r.md")
    text = out.read_text()
    assert text.startswith("# Title")
    assert "## Section" in text
    assert "hello" in text
