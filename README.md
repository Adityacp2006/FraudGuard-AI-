# 🛡️ FraudGuard AI

### Agentic Fraud Investigation System Powered by TigerGraph

> **Team Error Zero** · TigerGraph HHGOA Hackathon 2026

FraudGuard AI is an evidence-driven fraud investigation platform designed to help investigators analyze suspicious transactions, connect related entities, evaluate uncertainty, and determine the appropriate next-best action.

The system combines **TigerGraph, GSQL, Python, and Streamlit** to create a graph-based investigation workflow across transactions, customers, cards, identities, devices, and historical fraud cases.

---

## 🚀 Overview

Traditional fraud detection often starts and ends with a risk score.

**FraudGuard AI takes an investigation-first approach.**

When a transaction is flagged, the system gathers connected evidence from multiple sources and builds an investigation context around the transaction.

```text
                 Suspicious Transaction
                          │
                          ▼
                 ┌──────────────────┐
                 │   Investigation  │
                 │      Trigger     │
                 └────────┬─────────┘
                          │
                          ▼
              ┌─────────────────────────┐
              │       TigerGraph        │
              │   Connected Evidence    │
              └────────────┬────────────┘
                           │
          ┌────────────────┼────────────────┐
          ▼                ▼                ▼
      Customer           Card        Identity / Device
          │                │                │
          └────────────────┼────────────────┘
                           ▼
                  Historical Cases
                           │
                           ▼
                 Evidence Assessment
                           │
                           ▼
                  Fraud Probability
                           │
                           ▼
                Uncertainty Assessment
                           │
                 ┌─────────┴─────────┐
                 ▼                   ▼
          More Evidence          Decision
                 │                   │
                 └─────────┬─────────┘
                           ▼
                  Next Best Action
                           │
                           ▼
                 Investigation Case
