import os
import pandas as pd


transactions = pd.read_csv("data/transactions.csv")
identity = pd.read_csv("data/identity.csv")
cases = pd.read_csv("data/case_pack.csv")


def investigate(transaction_id):

    tx = transactions[
        transactions["TransactionID"] == int(transaction_id)
    ]

    if tx.empty:
        return {"error": "Transaction not found"}

    row = tx.iloc[0]

    risk = row["risk_score"]
    amount = float(row["TransactionAmt"])
    channel = row["channel"]
    product = row["ProductCD"]
    customer = row["customer_id"]

    if pd.isna(risk):
        risk = 0.30
    else:
        risk = float(risk)

    # Customer history
    customer_txns = transactions[
        transactions["customer_id"] == customer
    ]

    transaction_count = len(customer_txns)
    total_spend = customer_txns["TransactionAmt"].sum()
    average_spend = customer_txns["TransactionAmt"].mean()

    # Identity / device
    ident = identity[
        identity["TransactionID"] == int(transaction_id)
    ]

    device_info = "Not available"
    device_type = "Not available"
    shared_customers = 0

    if not ident.empty:

        device_info = str(ident.iloc[0]["DeviceInfo"])
        device_type = str(ident.iloc[0]["DeviceType"])

        device = ident.iloc[0]["DeviceInfo"]

        if pd.notna(device):

            device_rows = identity[
                identity["DeviceInfo"] == device
            ]

            tx_ids = device_rows["TransactionID"].unique()

            shared_customers = transactions[
                transactions["TransactionID"].isin(tx_ids)
            ]["customer_id"].nunique()

    # Fraud probability
    if risk >= 0.70:
        fraud_probability = min(risk + 0.10, 0.99)
    elif risk >= 0.30:
        fraud_probability = risk
    else:
        fraud_probability = max(risk - 0.05, 0.01)

    # Policy decision
    if fraud_probability >= 0.70:

        verdict = "LIKELY_FRAUD"
        action = "DECLINE_TRANSACTION"
        approval = "L1_TEAM_LEAD"

    elif fraud_probability >= 0.30:

        verdict = "UNCERTAIN"
        action = "VERIFY_WITH_CUSTOMER"
        approval = "AUTO"

    else:

        verdict = "LIKELY_LEGITIMATE"
        action = "ALLOW_TRANSACTION"
        approval = "AUTO"

    # Case creation policy
    create_case = fraud_probability >= 0.30

    # Evidence request
    if verdict == "UNCERTAIN":
        evidence_request = "VERIFY_WITH_CUSTOMER"
    else:
        evidence_request = "NONE"

    # SAR / reporting decision
    sar_file = (
        verdict == "LIKELY_FRAUD"
        and (
            amount > 1000
            or shared_customers > 1
        )
    )

    # Investigation summary
    if verdict == "LIKELY_FRAUD":
        summary = (
            f"Transaction {transaction_id} has elevated fraud probability "
            f"of {fraud_probability:.2f}. "
            f"Transaction amount is ${amount:.2f}. "
            f"Additional investigation and controlled action are required."
        )

    elif verdict == "UNCERTAIN":
        summary = (
            f"Transaction {transaction_id} has uncertain fraud probability "
            f"of {fraud_probability:.2f}. "
            f"Customer verification is recommended before stronger action."
        )

    else:
        summary = (
            f"Transaction {transaction_id} has low fraud probability "
            f"of {fraud_probability:.2f}. "
            f"No immediate fraud intervention is recommended."
        )

    return {
        "transaction_id": transaction_id,
        "customer_id": customer,
        "amount": round(amount, 2),
        "risk_score": round(risk, 2),
        "fraud_probability": round(fraud_probability, 2),
        "verdict": verdict,
        "channel": channel,
        "product": product,
        "transaction_count": transaction_count,
        "total_spend": round(total_spend, 2),
        "average_spend": round(average_spend, 2),
        "device_type": device_type,
        "device_info": device_info,
        "shared_customers": shared_customers,
        "create_case": create_case,
        "evidence_request": evidence_request,
        "next_best_action": action,
        "approval_route": approval,
        "sar_file": sar_file,
        "summary": summary
    }


# Run all 20 benchmark cases

results = []

print("\n===== FRAUDGUARD AI - 20 CASE BENCHMARK =====\n")

for _, case in cases.iterrows():

    result = investigate(case["flagged_txn_id"])

    result["case_id"] = case["case_id"]

    results.append(result)

    print(
        f"{case['case_id']} | "
        f"TXN: {result['transaction_id']} | "
        f"Customer: {result['customer_id']} | "
        f"Verdict: {result['verdict']} | "
        f"Action: {result['next_best_action']}"
    )


# Create report directory

os.makedirs("reports", exist_ok=True)


# Save benchmark results

report = pd.DataFrame(results)

report = report[
    [
        "case_id",
        "transaction_id",
        "customer_id",
        "amount",
        "risk_score",
        "fraud_probability",
        "verdict",
        "channel",
        "product",
        "transaction_count",
        "total_spend",
        "average_spend",
        "device_type",
        "device_info",
        "shared_customers",
        "create_case",
        "evidence_request",
        "next_best_action",
        "approval_route",
        "sar_file",
        "summary"
    ]
]

report.to_csv(
    "reports/benchmark_results.csv",
    index=False
)

print("\n======================================")
print("Benchmark completed successfully.")
print("Report saved to:")
print("reports\\benchmark_results.csv")
print("======================================")