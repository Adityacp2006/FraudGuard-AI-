import streamlit as st
from src.agent.fraud_agent_final import investigate


st.set_page_config(
    page_title="FraudGuard AI",
    page_icon="🛡️",
    layout="wide"
)


st.title("🛡️ FraudGuard AI")
st.subheader("Agentic Fraud Investigation System")

st.write(
    "Investigate a transaction using transaction, "
    "customer history, identity/device and prior-case evidence."
)


tx_id = st.text_input(
    "Enter Transaction ID",
    "3514030"
)


if st.button("Investigate Transaction"):

    result = investigate(tx_id)

    if "error" in result:

        st.error(result["error"])

    else:

        st.success("Investigation completed")

        col1, col2, col3, col4 = st.columns(4)

        col1.metric(
            "Fraud Probability",
            f"{result['fraud_probability']:.2f}"
        )

        col2.metric(
            "Transaction Amount",
            f"${result['amount']:.2f}"
        )

        col3.metric(
            "Customer Transactions",
            result["customer_transaction_count"]
        )

        col4.metric(
            "Shared Device Customers",
            result["shared_customers"]
        )

        st.divider()

        st.header("Investigation Result")

        st.write(
            f"**Verdict:** {result['verdict']}"
        )

        st.write(
            f"**Customer:** {result['customer_id']}"
        )

        st.write(
            f"**Channel:** {result['channel']}"
        )

        st.write(
            f"**Product:** {result['product']}"
        )

        st.divider()

        st.header("Evidence")

        c1, c2 = st.columns(2)

        with c1:

            st.write(
                "**Customer History**"
            )

            st.write(
                f"Transactions: "
                f"{result['customer_transaction_count']}"
            )

            st.write(
                f"Total spend: "
                f"${result['customer_total_spend']:,.2f}"
            )

            st.write(
                f"Average transaction: "
                f"${result['customer_average_spend']:,.2f}"
            )

        with c2:

            st.write(
                "**Identity / Device**"
            )

            st.write(
                f"Device type: "
                f"{result['device_type']}"
            )

            st.write(
                f"Device info: "
                f"{result['device_info']}"
            )

            st.write(
                f"Customers sharing device: "
                f"{result['shared_customers']}"
            )

        st.divider()

        st.header("Prior Case Memory")

        if result["similar_prior_cases"]:

            for case in result["similar_prior_cases"]:

                st.write(
                    f"**{case['case_id']}** | "
                    f"{case['outcome']} | "
                    f"{case['pattern']}"
                )

        else:

            st.write(
                "No previous cases found for this customer."
            )

        st.divider()

        st.header("Next Best Action")

        st.info(
            result["next_best_actions"]["final"]
        )

        st.write(
            f"Approval route: "
            f"**{result['approval_route']}**"
        )

        st.write(
            result["next_best_actions"]["what_changed"]
        )

        st.divider()

        st.header("Case Decision")

        st.write(
            f"Create case: "
            f"**{result['create_case']}**"
        )

        st.write(
            f"Evidence requested: "
            f"**{', '.join(result['evidence_requests']) if result['evidence_requests'] else 'None'}**"
        )

        st.divider()

        st.header("SAR / Reporting")

        st.write(
            f"File SAR: **{result['sar']['file']}**"
        )

        st.write(
            result["sar"]["reason"]
        )

        if result["sar"]["narrative"]:

            st.text_area(
                "SAR Narrative",
                result["sar"]["narrative"],
                height=150
            )

        st.divider()

        st.header("Investigation Summary")

        st.write(result["summary"])

        st.caption(
            "Graph write status: "
            f"{result['written_to_graph']}"
        )