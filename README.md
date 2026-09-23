# HHGOA Agentic Fraud Investigation — TigerGraph Hackathon Project

An agentic fraud-investigation system built for the **TigerGraph HHGOA hackathon**.
The finished agent will take a case from the case pack, investigate it using a
TigerGraph knowledge graph and prior closed cases, decide what kind of fraud
(if any) occurred, and recommend a next-best-action under the bank's fraud
policy — writing the completed case back into the graph as memory for future
investigations.

**This repository is currently in Phase 1.** No agent, no TigerGraph schema,
no GraphRAG and no frontend exist yet — on purpose. Phase 1 is only the
project foundation and dataset understanding, so every later phase is built
on verified facts about the data instead of assumptions.

---

## What Phase 1 delivers

1. A clean, modular Python project structure (below).
2. A Python virtual environment + pinned `requirements.txt`.
3. `.env.example` for configuration (dataset location, logging, and
   placeholders for later phases' API keys).
4. A `data/` folder for the HHGOA dataset (git-ignored — the dataset itself
   is not committed).
5. Scripts that:
   - read the dataset's own README/data-dictionary **first**, and locate
     (not invent) the sections describing: all files, transaction fields,
     customer/account information, device/connection information, previous
     fraud cases, the fraud policy, and the 20 benchmark cases;
   - profile every tabular file: row/column counts, missing values, data
     types, unique values, sample values, and top categorical values;
   - discover relationships between files by finding shared column names and
     measuring how much their values actually overlap.
6. A test suite (`pytest`) that exercises all of the above against a small
   synthetic dataset, so the tooling is verified even before the real HHGOA
   files are added.

**No fraud labels, column meanings, or entity relationships are assumed.**
Every claim in the generated reports is either quoted directly from the
dataset's README or computed directly from the dataset's own values.

---

## Project structure

```
hhgoa-fraud-agent/
├── data/                      # HHGOA dataset goes here (git-ignored)
│   └── .gitkeep
├── reports/                   # Generated inventory / profiling / relationship reports
│   └── .gitkeep
├── src/hhgoa_fraud/           # Installable package — Phase 1 modules live here
│   ├── config.py              # Settings, loaded from .env
│   ├── logging_utils.py       # Shared logger
│   ├── io_utils.py            # File discovery, table reading, key normalization
│   ├── row_count.py           # Exact, memory-light row counting
│   ├── readme_scan.py         # README discovery + section classification
│   ├── profiling.py           # Row/column/missing/dtype/unique profiling
│   ├── relationships.py       # Shared-column + value-overlap discovery
│   ├── reporting.py           # Markdown/JSON report writers
│   ├── agent/                 # (empty — Phase 4)
│   ├── graph/                 # (empty — Phase 2)
│   ├── rag/                   # (empty — Phase 4)
│   ├── policy/                # (empty — Phase 3/4)
│   └── memory/                # (empty — Phase 4)
├── scripts/                   # Runnable entry points (Phase 1)
│   ├── 00_check_setup.py
│   ├── 01_inspect_dataset.py
│   ├── 02_profile_dataset.py
│   ├── 03_explore_relationships.py
│   └── run_all.py
├── tests/                     # pytest suite, uses synthetic fixture data
├── graph/                     # (empty — Phase 2: GSQL schema & queries)
├── cases/                     # (empty — Phase 4/5: generated case outputs)
├── ui/                        # (empty — Phase 5: frontend)
├── docs/                      # (empty — architecture notes as they're written)
├── notebooks/                 # (empty — ad-hoc exploration, optional)
├── requirements.txt
├── pyproject.toml             # Packaging + pytest/ruff config
├── .env.example
├── .gitignore
├── setup.sh / setup.ps1       # One-shot environment setup
└── README.md
```

The empty folders (`graph/`, `agent/`, `rag/`, `policy/`, `memory/`, `ui/`,
`cases/`, `docs/`) exist now so the repository's target shape is visible from
day one, but nothing is implemented in them yet — that is intentional scope
control for Phase 1.

---

## Setup

### Prerequisites
- Python 3.10+
- VS Code with the Python extension (recommended extensions are listed in
  `.vscode/extensions.json` and will be suggested automatically)

### 1. Create the environment

**macOS / Linux**
```bash
chmod +x setup.sh
./setup.sh
```

**Windows (PowerShell)**
```powershell
.\setup.ps1
```

Either script will:
- create a `.venv` virtual environment,
- install `requirements.txt`,
- install this project in editable mode (`pip install -e .`) so `hhgoa_fraud`
  is importable from anywhere,
- copy `.env.example` to `.env` if `.env` doesn't already exist.

If you'd rather do it by hand:
```bash
python -m venv .venv
source .venv/bin/activate      # Windows: .venv\Scripts\Activate.ps1
pip install -r requirements.txt
pip install -e .
cp .env.example .env           # Windows: Copy-Item .env.example .env
```

### 2. Open in VS Code
Open the project folder in VS Code. It should auto-select the `.venv`
interpreter (via `.vscode/settings.json`). If not, run **Python: Select
Interpreter** and pick `.venv`.

### 3. Add the dataset
Place the HHGOA dataset files (CSVs, its README/data-dictionary, any policy
document, `case_pack.csv`, etc.) into `data/`. The scripts discover files
automatically — nothing needs to be renamed or restructured.

### 4. Run the checks
```bash
python scripts/00_check_setup.py        # sanity check: deps + data/ present
python scripts/01_inspect_dataset.py     # inventory + README category scan
python scripts/02_profile_dataset.py     # per-file profiling report
python scripts/03_explore_relationships.py  # cross-file relationship discovery
```
or run all four in order:
```bash
python scripts/run_all.py
```

Reports are written to `reports/` as both Markdown (human-readable) and JSON
(machine-readable, for later phases to consume).

### 5. Run the tests
```bash
pytest
```
The tests use a small synthetic dataset (see `tests/conftest.py`) so they
pass with or without the real HHGOA files present — this validates the
tooling itself, independent of what's actually in `data/`.

---

## What each script does

| Script | Purpose | Output |
|---|---|---|
| `00_check_setup.py` | Confirms dependencies import and `data/` exists; lists what's in it | console only |
| `01_inspect_dataset.py` | Lists every file; finds the dataset's own README and locates the sections covering files, transaction fields, customer/account info, device/connection info, previous fraud cases, fraud policy, and the 20 benchmark cases | `reports/01_dataset_inventory.md` / `.json` |
| `02_profile_dataset.py` | Rows, columns, dtypes, missing values (%), unique-value counts, sample values, and top categorical values for every tabular file. Handles large files (100s of MB) in bounded-memory chunks | `reports/profile_<file>.md` / `.json` + `reports/02_profiling_summary.md` |
| `03_explore_relationships.py` | Finds column names shared across files and measures how much their values actually overlap — evidence for how the entities (customers, cards, devices, cases) connect | `reports/03_relationships.md` / `.json` |
| `run_all.py` | Runs all four scripts above, in order | all of the above |

### Design choices worth knowing about

- **Only truly blank cells are treated as missing.** Text like `"NA"` or
  `"null"` is left as a real value and separately flagged as a "null-like
  token" count, because in some datasets those are legitimate categorical
  values (e.g. a country code) rather than missing data. Deciding whether to
  treat them as missing is a data-understanding decision for a human to make
  after reading the profiling report — the tooling won't make that call
  silently.
- **Large files are read in row- and column-chunks**, so profiling a
  multi-hundred-MB transactions file doesn't require loading it all into
  memory at once.
- **Very high-cardinality columns** (e.g. transaction IDs) stop tracking an
  exact unique-value set past a configurable cap (`200,000` by default) to
  avoid unbounded memory use; the report shows this as a `N+` lower bound
  instead of silently guessing.
- **Relationship discovery is evidence-based, not assumed.** A column name
  appearing in two files is only a *candidate* key; the actual overlap
  percentage of real values is computed and shown so you can judge whether
  it's a genuine join.

---

## Configuration (`.env`)

See `.env.example` for the full list with comments. The Phase 1-relevant
settings are:

| Variable | Default | Meaning |
|---|---|---|
| `DATA_DIR` | `data` | Where the dataset lives |
| `REPORTS_DIR` | `reports` | Where generated reports are written |
| `LOG_LEVEL` | `INFO` | Logging verbosity |
| `LARGE_FILE_MB` | `150` | Threshold for "large file" handling |
| `COLUMN_BATCH_SIZE` | `60` | Columns profiled per pass, for wide files |
| `LOW_CARDINALITY_MAX` | `25` | Columns at/below this get full top-value counts |
| `CSV_ENGINE` | `c` | `c` (predictable) or `pyarrow` (faster, auto-fallback to `c`) |

The remaining variables (`TG_HOST`, `TG_SECRET`, `ANTHROPIC_API_KEY`, ...) are
placeholders for later phases and are not read by any Phase 1 code.

---

## Roadmap (later phases — not built yet)

- **Phase 2 — TigerGraph schema & loading**: design the graph schema
  (Customer, Card, Transaction, Device, ClosedCase, InvestigationCase, etc.,
  informed by the relationships discovered in Phase 1) and load the dataset
  into TigerGraph.
- **Phase 3 — Policy encoding**: formalize the bank's fraud policy rules
  (read directly from the dataset's policy document) into a structured,
  checkable form.
- **Phase 4 — Agent + GraphRAG**: build the investigation agent that queries
  the graph, retrieves prior case memory, reasons about fraud patterns,
  handles uncertainty, and recommends a next-best-action grounded in graph
  facts and policy rules — not free-standing LLM guesses.
- **Phase 5 — Frontend / analyst UI**: an interface for running and
  reviewing investigations end-to-end, including the 20 benchmark cases.

Each phase should be able to point back to this Phase 1 output (the README
category scan, the profiling reports, the relationship reports) as its
source of truth about what the data actually contains.

---

## Phase 2 status: dataset and join validation complete

Phase 2 has validated the actual join structure of the HHGOA dataset
(`transactions.csv`, `identity.csv`, `case_pack.csv`,
`closed_cases_history.csv`) against `data/README.md`, and documented a
canonical logical data model. **No TigerGraph schema, no agent, no
GraphRAG, and no Streamlit UI exist yet — Phase 2 is documentation and
validation only, same scope discipline as Phase 1.**

What was verified (full detail in `reports/join_validation.md` and
`reports/data_quality.md`):

- `customer_id` <-> `card1` is one-to-one in `transactions.csv` (13,553
  unique values each side).
- 20/20 `case_pack.csv` benchmark cases join to `transactions.csv` on both
  `flagged_txn_id` and `customer_id`.
- 5,565/5,565 `closed_cases_history.csv` customers join to
  `transactions.csv` on `customer_id`.
- 144,432 transactions have a matching `identity.csv` record (online-only,
  by design).
- `DeviceInfo` sharing across customers is measured (1,786 unique values,
  1,237 shared, max 4,846 customers on one value) and documented as an
  investigation *signal*, not a fraud indicator.
- `TransactionID`, `customer_id`, `ts`, `channel`, `risk_score` have zero
  missing values.
- `HistoricalCase -> Transaction`/`Card` joins were **not** checked this
  phase — see `reports/join_validation.md` §4 before relying on them.

New Phase 2 deliverables:

| File | Purpose |
|---|---|
| `reports/dataset_inventory.md` | All files, row/column counts, field-to-entity mapping |
| `reports/canonical_data_model.md` | Logical entities (Customer, Card, Transaction, Device, IdentityRecord, InvestigationCase, HistoricalCase, FraudPattern, PolicyRule, Evidence) and evidence-backed relationships, each labeled stored vs. derived. Includes R1–R10 verbatim |
| `reports/join_validation.md` | The actual validation results |
| `reports/data_quality.md` | Completeness, coverage, and caveats |
| `src/data/validate_joins.py` | Reusable, column-scoped validation script (`python -m data.validate_joins --data-dir data`) |
| `tests/test_data_validation.py` | pytest coverage of the join/uniqueness logic against small synthetic fixtures (no full-file loads) |

Next phase (not started): **Phase 3 — TigerGraph schema & loading**, per the
roadmap above.
