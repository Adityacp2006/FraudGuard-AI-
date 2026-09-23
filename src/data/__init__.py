"""Phase 2 — canonical data model & join validation.

Separate from ``hhgoa_fraud`` (Phase 1's dataset-agnostic profiling tools).
This package is deliberately HHGOA-schema-aware: it uses the real column
names (`TransactionID`, `customer_id`, `card1`, `DeviceInfo`, ...) documented
in `data/README.md`, because Phase 2's job is to validate the *specific*
joins this dataset claims to have, not to discover schema generically.
"""
