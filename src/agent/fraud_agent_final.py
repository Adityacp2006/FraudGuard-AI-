import os
import json
import pandas as pd


# =========================
# LOAD DATA
# =========================

transactions = pd.read_csv("data/transactions.csv")
identity = pd.read_csv("data/identity.csv")
cases = pd.read_csv("data/case_pack.csv")
history = pd.read_csv("data/closed_cases_history.csv")


# =========================
# INVESTIGATION FUNCTION
# =========================

def investigate(transaction_id):

    tx = transactions[
        transactions["TransactionID"] == int(transaction_id)
    ]

    if tx.empty:
        return {"error": "Transaction not found"}

    row = tx.iloc[0]

    customer = row["customer_id"]
    amount = float(row["TransactionAmt"])
    channel = row["channel"]
    product = row["ProductCD"]

    risk = row["risk_score"]

    if pd.isna(risk):
        risk = 0.30
    else:
        risk = float(risk)

    # -------------------------
    # Fraud probability
    # -------------------------

    if risk >= 0.70:
        fraud_probability = min(risk + 0.10, 0.99)
    elif risk >= 0.30:
        fraud_probability = risk
    else:
        fraud_probability = max(risk - 0.05, 0.01)

    # -------------------------
    # Customer history
    # -------------------------

    customer_txns = transactions[
        transactions["customer_id"] == customer
    ]

    transaction_count = len(customer_txns)
    total_spend = customer_txns["TransactionAmt"].sum()
    average_spend = customer_txns["TransactionAmt"].mean()

    # -------------------------
    # Previous cases / memory
    # -------------------------

    customer_cases = history[
        history["customer_id"] == customer
    ]

    prior_cases = []

    for _, c in customer_cases.head(5).iterrows():

        prior_cases.append({
            "case_id": str(c["case_id"]),
            "outcome": str(c["outcome"]),
            "pattern": str(c["pattern"]),
            "exposure_usd": float(c["exposure_usd"])
            if pd.notna(c["exposure_usd"]) else 0
        })

    # -------------------------
    # Identity / device
    # -------------------------

    ident = identity[
        identity["TransactionID"] == int(transaction_id)
    ]

    device_type = "Not available"
    device_info = "Not available"
    shared_customers = 0

    if not ident.empty:

        device_type = str(
            ident.iloc[0]["DeviceType"]
        )

        device = ident.iloc[0]["DeviceInfo"]

        if pd.notna(device):

            device_info = str(device)

            device_rows = identity[
                identity["DeviceInfo"] == device
            ]

            tx_ids = device_rows["TransactionID"].unique()

            shared_customers = transactions[
                transactions["TransactionID"].isin(tx_ids)
            ]["customer_id"].nunique()

    # -------------------------
    # Verdict
    # -------------------------

    if fraud_probability >= 0.70:

        verdict = "LIKELY_FRAUD"

    elif fraud_probability >= 0.30:

        verdict = "UNCERTAIN"

    else:

        verdict = "LIKELY_LEGITIMATE"

    # -------------------------
    # Next best action
    # -------------------------

    if verdict == "LIKELY_FRAUD":

        initial_action = "DECLINE_TRANSACTION"
        final_action = "DECLINE_TRANSACTION"
        approval = "L1_TEAM_LEAD"

    elif verdict == "UNCERTAIN":

        initial_action = "VERIFY_WITH_CUSTOMER"

        if amount > 500:

            final_action = "ESCALATE_TO_ANALYST"
            approval = "AUTO"

        else:

            final_action = "VERIFY_WITH_CUSTOMER"
            approval = "AUTO"

    else:

        initial_action = "ALLOW_TRANSACTION"
        final_action = "ALLOW_TRANSACTION"
        approval = "AUTO"

    # -------------------------
    # Evidence requests
    # -------------------------

    evidence_requests = []

    if verdict == "UNCERTAIN":
        evidence_requests.append(
            "VERIFY_WITH_CUSTOMER"
        )

    # -------------------------
    # Case creation
    # -------------------------

    create_case = (
        fraud_probability >= 0.30
        or len(evidence_requests) > 0
    )

    # -------------------------
    # SAR decision
    # -------------------------

    # Do NOT automatically file SAR simply
    # because a generic device is shared.

    sar_file = False
    sar_reason = "No sufficient evidence for automatic SAR filing."

    if verdict == "LIKELY_FRAUD" and amount > 1000:

        sar_file = True

        sar_reason = (
            "Likely fraud with transaction exposure "
            "above $1,000."
        )

    # -------------------------
    # Summary
    # -------------------------

    summary = (
        f"Transaction {transaction_id} for customer "
        f"{customer} was investigated using transaction, "
        f"customer-history, identity/device and prior-case "
        f"evidence. Fraud probability is "
        f"{fraud_probability:.2f}. "
        f"Final assessment: {verdict}."
    )

    # -------------------------
    # What changed
    # -------------------------

    if initial_action != final_action:

        what_changed = (
            f"Initial action was {initial_action}. "
            f"Because transaction exposure is "
            f"${amount:.2f}, the policy escalated "
            f"the final action to {final_action}."
        )

    else:

        what_changed = (
            "No change after additional evidence review."
        )

    # -------------------------
    # SAR narrative
    # -------------------------

    if sar_file:

        sar_narrative = (
            f"Transaction {transaction_id} associated with "
            f"customer {customer} was assessed as likely "
            f"fraudulent with probability "
            f"{fraud_probability:.2f}. "
            f"The transaction amount was "
            f"${amount:.2f}. "
            f"The case requires reporting review."
        )

    else:

        sar_narrative = ""

    return {

        "transaction_id": str(transaction_id),

        "customer_id": str(customer),

        "amount": round(amount, 2),

        "risk_score": round(risk, 2),

        "fraud_probability":
            round(fraud_probability, 2),

        "verdict": verdict,

        "channel": channel,

        "product": product,

        "customer_transaction_count":
            transaction_count,

        "customer_total_spend":
            round(total_spend, 2),

        "customer_average_spend":
            round(average_spend, 2),

        "device_type": device_type,

        "device_info": device_info,

        "shared_customers":
            int(shared_customers),

        "similar_prior_cases":
            prior_cases,

        "create_case":
            create_case,

        "evidence_requests":
            evidence_requests,

        "next_best_actions": {

            "initial": initial_action,

            "final": final_action,

            "what_changed": what_changed

        },

        "approval_route":
            approval,

        "sar": {

            "file": sar_file,

            "reason": sar_reason,

            "narrative": sar_narrative

        },

        "written_to_graph": False,

        "graph_case_id": None,

        "summary": summary
    }


# =========================
# RUN 20 BENCHMARK CASES
# =========================

results = []

print("\n==========================================")
print(" FRAUDGUARD AI - FINAL 20 CASE BENCHMARK")
print("==========================================\n")


for _, case in cases.iterrows():

    result = investigate(
        case["flagged_txn_id"]
    )

    result["case_id"] = case["case_id"]

    results.append(result)

    print(
        f"{case['case_id']} | "
        f"{result['verdict']} | "
        f"{result['next_best_actions']['final']}"
    )


# =========================
# SAVE REPORTS
# =========================

os.makedirs("reports", exist_ok=True)


with open(
    "reports/benchmark_final.json",
    "w",
    encoding="utf-8"
) as f:

    json.dump(
        results,
        f,
        indent=2
    )


rows = []

for r in results:

    rows.append({

        "case_id":
            r["case_id"],

        "transaction_id":
            r["transaction_id"],

        "customer_id":
            r["customer_id"],

        "fraud_probability":
            r["fraud_probability"],

        "verdict":
            r["verdict"],

        "initial_action":
            r["next_best_actions"]["initial"],

        "final_action":
            r["next_best_actions"]["final"],

        "approval_route":
            r["approval_route"],

        "create_case":
            r["create_case"],

        "prior_cases":
            len(r["similar_prior_cases"]),

        "device_info":
            r["device_info"],

        "shared_customers":
            r["shared_customers"],

        "sar_file":
            r["sar"]["file"]

    })


pd.DataFrame(rows).to_csv(
    "reports/benchmark_final.csv",
    index=False
)


print("\n==========================================")
print(" FINAL BENCHMARK COMPLETED")
print("==========================================")
print("Saved:")
print("reports\\benchmark_final.csv")
print("reports\\benchmark_final.json")
print("==========================================")