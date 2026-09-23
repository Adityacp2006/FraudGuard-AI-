"""Find the dataset's own README/docs and point at the parts relevant to each
required category (files, transaction fields, customer/account info, device
info, past fraud cases, fraud policy, the 20 benchmark cases).

This is a heuristic *locator*, not a parser that invents structure: it splits
the document into sections by heading and keyword-matches each section, so a
human (or a later phase) can go read the exact section instead of trusting a
guess. Nothing here fabricates column names or definitions that are not in
the text.
"""

from __future__ import annotations

import re
from dataclasses import dataclass
from pathlib import Path

from .io_utils import FileInfo

README_NAME_HINTS = ("readme", "read_me", "data_dictionary", "datadictionary", "dictionary", "policy", "data_card")

CATEGORY_KEYWORDS: dict[str, list[str]] = {
    "files": ["file", "csv", "dataset consists", "directory", "folder"],
    "transaction_fields": ["transaction", "txn", "amount", "purchase", "card", "merchant", "currency"],
    "customer_account": ["customer", "account", "cardholder", "billing", "email domain", "identity"],
    "device_connection": ["device", "ip address", "browser", "connection", "network", "user agent", "fingerprint"],
    "previous_fraud_cases": ["closed case", "case history", "prior case", "past case", "historical case", "resolved"],
    "fraud_policy": ["policy", "rule r", "sar", "suspicious activity report", "escalation", "approval", "compliance"],
    "benchmark_cases": ["benchmark", "case pack", "20 case", "evaluation set", "scoring", "answer format", "hhg-"],
}


@dataclass
class ReadmeSection:
    heading: str
    level: int
    line_start: int
    text: str


@dataclass
class ReadmeCategoryMatch:
    category: str
    heading: str
    line_start: int
    snippet: str


@dataclass
class ReadmeScanResult:
    path: str | None
    sections: list[ReadmeSection]
    matches: list[ReadmeCategoryMatch]
    unmatched_categories: list[str]


_HEADING_RE = re.compile(r"^(#{1,6})\s+(.*)$")


def find_readme_files(data_dir: Path) -> list[FileInfo]:
    """Every document file under data_dir whose name looks like a README/policy doc."""
    from .io_utils import discover_files

    candidates = []
    for info in discover_files(data_dir):
        if info.kind != "document":
            continue
        stem = info.path.stem.lower()
        if any(hint in stem for hint in README_NAME_HINTS):
            candidates.append(info)
    # Put the most obviously-named README first.
    candidates.sort(key=lambda i: (0 if "readme" in i.path.stem.lower() else 1, i.rel))
    return candidates


def _read_text(info: FileInfo) -> str:
    if info.suffix == ".pdf":
        from pypdf import PdfReader

        reader = PdfReader(str(info.path))
        return "\n".join(page.extract_text() or "" for page in reader.pages)
    return info.path.read_text(encoding="utf-8", errors="replace")


def split_into_sections(text: str) -> list[ReadmeSection]:
    """Split Markdown/plain text into sections at each heading line.

    For plain text without Markdown headings, the whole document becomes one
    section so it is still scanned for keywords.
    """
    lines = text.splitlines()
    headings = [(i, m.group(1), m.group(2).strip()) for i, line in enumerate(lines) if (m := _HEADING_RE.match(line))]

    if not headings:
        return [ReadmeSection(heading="(document)", level=0, line_start=0, text=text)]

    sections: list[ReadmeSection] = []
    if headings[0][0] > 0:
        preamble = "\n".join(lines[: headings[0][0]])
        sections.append(ReadmeSection(heading="(preamble)", level=0, line_start=0, text=preamble))

    for idx, (line_no, hashes, title) in enumerate(headings):
        end = headings[idx + 1][0] if idx + 1 < len(headings) else len(lines)
        body = "\n".join(lines[line_no + 1 : end]).strip()  # exclude the heading line itself
        sections.append(ReadmeSection(heading=title, level=len(hashes), line_start=line_no, text=body))
    return sections


def classify_sections(sections: list[ReadmeSection]) -> tuple[list[ReadmeCategoryMatch], list[str]]:
    matches: list[ReadmeCategoryMatch] = []
    matched_categories: set[str] = set()

    for section in sections:
        haystack = f"{section.heading}\n{section.text}".lower()
        for category, keywords in CATEGORY_KEYWORDS.items():
            if any(kw in haystack for kw in keywords):
                snippet = section.text.strip()
                if len(snippet) > 600:
                    snippet = snippet[:600].rsplit(" ", 1)[0] + " …"
                matches.append(
                    ReadmeCategoryMatch(
                        category=category,
                        heading=section.heading,
                        line_start=section.line_start,
                        snippet=snippet,
                    )
                )
                matched_categories.add(category)

    unmatched = [c for c in CATEGORY_KEYWORDS if c not in matched_categories]
    return matches, unmatched


def scan_readme(data_dir: Path) -> ReadmeScanResult:
    candidates = find_readme_files(data_dir)
    if not candidates:
        return ReadmeScanResult(path=None, sections=[], matches=[], unmatched_categories=list(CATEGORY_KEYWORDS))

    info = candidates[0]
    text = _read_text(info)
    sections = split_into_sections(text)
    matches, unmatched = classify_sections(sections)
    return ReadmeScanResult(path=info.rel, sections=sections, matches=matches, unmatched_categories=unmatched)
