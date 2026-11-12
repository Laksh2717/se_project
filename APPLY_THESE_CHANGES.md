# Batch 1: how to apply

1. Copy everything in this folder over the repo root (replace existing files).
2. Delete these from the repo:
   - tests/test_basic_wallet_flow.py, tests/test_health.py, tests/test_reversal_flow.py,
     tests/test_wallet_entries_and_admin.py, tests/test_wallet_validation.py
   - financial_ledger.db  (old schema: it has no constraints or funding wallets; a new one is created on start)
   - PROJECT_SUMMARY.md, REQUIREMENT_STATUS_REPORT.md
3. Run:  pip install -r requirements.txt   then   pytest
   Expected: 60 passed.
4. Push, then tell Claude.
