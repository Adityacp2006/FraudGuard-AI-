# FraudGuard AI — Agentic Fraud Investigation System

> TigerGraph HHGOA Hackathon 2026 Project

FraudGuard AI is a fraud investigation system designed to help analysts investigate suspicious banking transactions using transaction behavior, customer history, identity and device signals, previous investigation cases, and fraud policy rules.

The project combines Python-based investigation logic, TigerGraph graph modeling, GSQL investigation queries, and a Streamlit dashboard to provide an end-to-end fraud investigation workflow.

---

## Project Overview

Fraud investigations often require analysts to examine information from multiple sources before deciding what action should be taken.

FraudGuard AI brings these signals together into a single investigation workflow.

### Core capabilities

* Transaction-level fraud investigation
* Customer transaction history analysis
* Identity and device evidence
* Shared-device analysis
* Fraud probability estimation
* Prior closed-case investigation memory
* Policy-based next-best-action recommendation
* Investigation case creation logic
* SAR/report decision logic
* TigerGraph graph investigation
* Interactive Streamlit dashboard
* Evaluation across 20 benchmark cases

---

## Architecture

```text
                    ┌──────────────────────┐
                    │    Benchmark Case    │
                    │     / Transaction    │
                    └──────────┬───────────┘
                               │
                               ▼
                    ┌──────────────────────┐
                    │    FraudGuard AI     │
                    │  Investigation Engine │
                    └──────────┬───────────┘
                               │
              ┌────────────────┼────────────────┐
              │                │                │
              ▼                ▼                ▼
       ┌────────────┐   ┌────────────┐   ┌────────────┐
       │Transaction │   │ Customer   │   │ Identity & │
       │   Data     │   │  History   │   │   Device   │
       └────────────┘   └────────────┘   └────────────┘
              │                │                │
              └────────────────┼────────────────┘
                               ▼
                    ┌──────────────────────┐
                    │   Evidence Analysis  │
                    │ + Fraud Probability  │
                    └──────────┬───────────┘
                               │
                               ▼
                    ┌──────────────────────┐
                    │    Fraud Policy      │
                    │   & Uncertainty      │
                    └──────────┬───────────┘
                               │
                               ▼
                    ┌──────────────────────┐
                    │    Next Best Action  │
                    └──────────┬───────────┘
                               │
              ┌────────────────┼────────────────┐
              ▼                ▼                ▼
        ┌──────────┐    ┌──────────────┐   ┌──────────┐
        │   Case   │    │   Analyst    │   │   SAR /  │
        │ Creation │    │  Escalation  │   │  Report  │
        └──────────┘    └──────────────┘   └──────────┘

```

---

## Dataset

The project uses the HHGOA fraud investigation dataset provided for the TigerGraph hackathon.

The verified project data includes:

| File                       | Records |
| -------------------------- | ------: |
| `transactions.csv`         | 590,742 |
| `identity.csv`             | 144,432 |
| `case_pack.csv`            |      20 |
| `closed_cases_history.csv` |   5,565 |

### Important validated relationships

* All 20 benchmark `flagged_txn_id` values were found in `transactions.csv`.
* All 20 benchmark `customer_id` values were found in `transactions.csv`.
* All 5,565 historical-case customers were found in transaction data.
* 144,432 transactions have matching identity records.
* `customer_id` and `card1` form a one-to-one mapping in the verified transaction data.
* Shared `DeviceInfo` values are treated as investigation signals rather than automatic evidence of fraud.

The complete validation details are available in the `reports/` directory.

---

## Investigation Workflow

FraudGuard AI follows this workflow:

```text
Trigger
   ↓
Transaction Investigation
   ↓
Customer History
   ↓
Identity / Device Evidence
   ↓
Prior Case Memory
   ↓
Fraud Probability
   ↓
Uncertainty Assessment
   ↓
Policy Evaluation
   ↓
Next Best Action
   ↓
Case / Report / Escalation

```

---

## TigerGraph Implementation

A dedicated TigerGraph graph was created for the investigation system:

```text
HHGOA_Fraud_Investigation

```

### Main vertices

```text
Customer
Card
Transaction
Device
Identity
FraudCase
HistoricalCase

```

### Main relationships

```text
Customer ──OWNS──────────────> Card
Customer ──MADE──────────────> Transaction
Transaction ──USES_CARD──────> Card
Transaction ──HAS_IDENTITY───> Identity
Customer ──HAS_CASE──────────> FraudCase
FraudCase ──INVOLVES─────────> Transaction
Customer ──HAS_HISTORY───────> HistoricalCase

```

### Investigation query

The project includes a GSQL investigation query:

```text
investigate_transaction(transaction_id)

```

Example:

```text
RUN QUERY investigate_transaction("3514030")

```

The query retrieves connected:

* Transaction
* Customer
* Card
* Identity

information for investigation.

---

## Fraud Investigation Evidence

For each investigated transaction, FraudGuard AI considers available evidence such as:

### Transaction evidence

* Transaction amount
* Product category
* Transaction channel
* Email domains
* Address information
* Risk score
* Transaction timestamp

### Customer evidence

* Total transaction count
* Historical spending behavior
* Average transaction amount
* Customer transaction patterns

### Identity and device evidence

* Device information
* Device type
* Shared device relationships
* Number of customers associated with a device

### Case memory

* Previous closed cases
* Previous investigation outcomes
* Fraud patterns
* Historical exposure
* Previous analyst notes

---

## Fraud Policy

The investigation workflow incorporates the dataset's documented fraud policy.

Example policy-driven actions include:

```text
ALLOW_TRANSACTION
DECLINE_TRANSACTION
MONITOR_CARD
MONITOR_CONNECTED_CARDS
WARN_CUSTOMER
VERIFY_WITH_CUSTOMER
STEP_UP_AUTH
BLOCK_CARD
BLOCK_ALL_CARDS
CREATE_CASE
GENERATE_REPORT
FILE_REPORT
ESCALATE_TO_ANALYST
CLOSE_NO_FRAUD

```

The system distinguishes between actions that can be automatically recommended and actions that require human approval.

### Approval routing

```text
Agent
  │
  ├── Automatic actions
  │
  ├── L1 Team Lead approval
  │
  └── L2 Fraud Manager approval

```

The agent recommends actions while higher-risk actions can be routed for human approval.

---

## Uncertainty Handling

FraudGuard AI does not treat every suspicious transaction as confirmed fraud.

The investigation can produce three high-level outcomes:

```text
LIKELY_FRAUD
UNCERTAIN
LIKELY_LEGITIMATE

```

For uncertain investigations, the system can request additional evidence such as customer verification before recommending stronger action.

This allows the investigation workflow to distinguish between:

* Strong evidence
* Weak evidence
* Conflicting evidence
* Missing evidence
* High-exposure uncertain cases

---

## Streamlit Dashboard

The project includes an interactive Streamlit dashboard for analysts.

Run it with:

```bash
streamlit run app.py

```

The dashboard provides:

* Transaction ID search
* Fraud probability
* Transaction details
* Customer information
* Customer transaction history
* Identity and device evidence
* Shared-device information
* Prior case memory
* Investigation verdict
* Next-best action
* Approval route
* Case creation status
* Evidence requests
* SAR/report decision

---

## Example Investigation

Example transaction:

```text
Transaction ID: 3514030
Customer ID: C12382
Amount: $77.07
Channel: in_person
Product: W
Fraud Probability: 0.61
Verdict: UNCERTAIN

```

The system identifies the case as uncertain and recommends additional verification rather than immediately treating the transaction as confirmed fraud.

---

## Benchmark Evaluation

FraudGuard AI was executed against all **20 benchmark cases** from the case pack.

The final benchmark output is generated as:

```text
reports/
├── benchmark_final.csv
└── benchmark_final.json

```

The output contains investigation information including:

* Case ID
* Transaction ID
* Fraud probability
* Verdict
* Similar prior cases
* Investigation summary
* Evidence requests
* Initial next-best action
* Final next-best action
* Explanation of what changed
* SAR decision
* SAR reason/narrative
* Graph write status

---

## Project Structure

```text
fraud-hack-/
│
├── app.py
├── requirements.txt
├── pyproject.toml
├── README.md
├── .env.example
├── .gitignore
│
├── data/
│   ├── transactions.csv
│   ├── identity.csv
│   ├── case_pack.csv
│   ├── closed_cases_history.csv
│   └── README.md
│
├── graph/
│   ├── schema/
│   │   └── fraud_graph.gsql
│   └── queries/
│
├── reports/
│   ├── dataset_inventory.md
│   ├── canonical_data_model.md
│   ├── join_validation.md
│   ├── data_quality.md
│   ├── benchmark_final.csv
│   └── benchmark_final.json
│
├── scripts/
│
├── src/
│   ├── agent/
│   ├── data/
│   └── hhgoa_fraud/
│
├── tests/
│
└── ui/

```

---

## Installation

### 1. Clone the repository

```bash
git clone https://github.com/Adityacp2006/fraud-hack-.git
cd fraud-hack-

```

### 2. Create a virtual environment

Windows:

```bash
python -m venv .venv
.venv\Scripts\activate

```

### 3. Install dependencies

```bash
pip install -r requirements.txt

```

### 4. Configure environment variables

Create a `.env` file based on:

```text
.env.example

```

Do not commit `.env` or any secret credentials.

---

## Running the Application

Start the Streamlit dashboard:

```bash
streamlit run app.py

```

Then open the local Streamlit URL shown in the terminal.

---

## Running Tests

Run:

```bash
pytest -q

```

The project validation test suite contains **36 passing tests**.

---

## Validation

The project completed data and join validation before graph and agent development.

Verified results include:

```text
20/20 benchmark transactions connected
20/20 benchmark customers connected
5565/5565 historical customers connected
144432 identity records connected
13553 unique customer-card mappings

```

These checks help ensure that investigation relationships are based on actual dataset values rather than assumed relationships.

---

## Security

Sensitive credentials are intentionally excluded from the repository.

The `.gitignore` protects:

```text
.env
.venv/
__pycache__/
*.pyc
.streamlit/

```

API keys, passwords, and private credentials should never be committed to GitHub.

---

## Current MVP Status

### Completed

* Dataset inspection
* Dataset profiling
* Join validation
* Canonical data model
* TigerGraph schema
* TigerGraph data loading
* GSQL investigation query
* Customer transaction investigation
* Identity investigation
* Prior case memory
* Fraud investigation agent
* Next-best-action logic
* SAR decision logic
* 20-case benchmark execution
* Streamlit dashboard
* Automated tests
* GitHub repository

### Future enhancements

* Full TigerGraph MCP integration
* Production-grade LLM reasoning
* GraphRAG policy retrieval
* Real-time transaction streaming
* Analyst feedback loop
* Production deployment

---

## Technology Stack

* **Python**
* **Pandas**
* **TigerGraph**
* **GSQL**
* **Streamlit**
* **Pytest**
* **Git / GitHub**

---

## Hackathon Goal

FraudGuard AI is designed around the following investigation loop:

```text
Trigger
   ↓
Investigate
   ↓
Gather Evidence
   ↓
Assess Uncertainty
   ↓
Gather More Evidence
   ↓
Recommend Action
   ↓
Explain Decision
   ↓
Update Case Memory

```

The goal is to provide investigators with an explainable, evidence-driven workflow rather than relying on a single risk score.

---

## Team

### Team Error Zero

**Team Members:**

* **Aditya Chander Pandey**
* **Shilpa**
* **Vanshika**

**Project:** FraudGuard AI — Agentic Fraud Investigation System

**Hackathon:** TigerGraph HHGOA Hackathon 2026

---

## Disclaimer

This project is a hackathon/educational prototype and is not intended for direct use in production banking or financial decision-making systems without appropriate validation, security controls, compliance review, and human oversight.
