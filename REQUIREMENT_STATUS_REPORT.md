# Requirement-by-Requirement Status Report

This report compares the original SRS in `SRS_DOCUMENT.pdf` with the current codebase in the workspace. It is based on direct reading of the SRS text and the current implementation in `app/` and `tests/`.

Important note:
- The requirement IDs were extracted from the SRS PDF.
- Some generic NFR/BR/SK/TQ items are broad statements rather than fully detailed sentence-level clauses in the extracted text.
- Where the exact wording was not fully readable in the PDF text extraction, the conclusion is based on direct code evidence and is marked as such in the notes below.

## Requirement Status Table

| ID | Status | Evidence | Deviation | Effort if not done |
|---|---|---|---|---|
| FR-1.1 | Implemented | `app/api/routes/users.py::create_user` | None observed | — |
| FR-1.2 | Implemented | `app/api/routes/wallets.py::create_wallet` | None observed | — |
| FR-1.3 | Implemented | `app/api/routes/wallets.py::create_wallet` | None observed | — |
| FR-1.4 | Implemented | `app/api/routes/wallets.py::create_wallet` | None observed | — |
| FR-1.5 | Implemented | `app/models/ledger_entry.py`, `app/services/ledger_service.py::_append_ledger_entry` | None observed | — |
| FR-1.6 | Partial | `app/services/ledger_service.py::deposit` | No system funding account is debited; deposit credits the wallet directly | Small |
| FR-1.7 | Implemented | `app/services/ledger_service.py::deposit` | Deposit is direct-credit logic, not balanced system-account funding | Small |
| FR-1.8 | Partial | `app/services/ledger_service.py::deposit` | No separate system funding account or balancing account exists | Small |
| FR-1.9 | Implemented | `app/schemas/transaction.py::DepositRequest` and validation path | Validation is Pydantic-based 422/validation failure rather than custom SRS wording | — |
| FR-2.1 | Partial | `app/api/routes/transactions.py::make_transfer` | Idempotency key is in the JSON body, not an HTTP header; missing key fails as 422, not 400 | Small |
| FR-2.2 | Implemented | `app/services/ledger_service.py::transfer` | None observed | — |
| FR-2.3 | Partial | `app/services/ledger_service.py::transfer` | Same-currency and sufficient-funds rules are enforced; no `BEGIN IMMEDIATE` or explicit concurrency lock is used | Small |
| FR-2.4 | Implemented | `app/services/ledger_service.py::transfer` | None observed | — |
| FR-2.5 | Implemented | `app/services/ledger_service.py::transfer` | None observed | — |
| FR-2.6 | Implemented | `app/services/ledger_service.py::transfer` | None observed | — |
| FR-2.7 | Implemented | `app/services/ledger_service.py::transfer` | None observed | — |
| FR-2.8 | Implemented | `app/models/idempotency_key.py` | None observed | — |
| FR-2.9 | Implemented | `app/services/ledger_service.py::transfer` | Same request replay returns stored response | — |
| FR-2.10 | Implemented | `app/services/ledger_service.py::transfer` | Safe replay path is implemented | — |
| FR-2.11 | Implemented | `app/services/ledger_service.py::transfer` | Conflict on reused key with different payload is implemented | — |
| FR-2.12 | Implemented | `app/services/ledger_service.py::transfer` | None observed | — |
| FR-2.13 | Partial | `app/services/ledger_service.py::transfer` | Multi-request concurrency safety is not enforced via `BEGIN IMMEDIATE`; only WAL + busy timeout are used | Small |
| FR-3.1 | Partial | `app/database.py` and `app/services/ledger_service.py` | No `BEGIN IMMEDIATE`; SQLAlchemy default transaction mode is used, not explicit concurrency locking | Small |
| FR-3.2 | Partial | `app/database.py` | WAL + busy timeout set, but no explicit SQLite concurrency policy beyond that | Small |
| FR-3.3 | Partial | `app/database.py` | No app-level lock or transaction conflict handling is implemented | Small |
| FR-3.4 | Partial | `app/database.py` | No explicit retry/503/Retry-After behavior in the API | Small |
| FR-3.5 | Partial | `app/database.py` | No `busy_timeout` handling in HTTP layer; no 503 status | Small |
| FR-3.6 | Partial | `app/database.py` | No deterministic race test coverage in code/tests | Small |
| FR-3.7 | Partial | `tests/` directory | No concurrency test file exists | Small |
| FR-3.8 | Partial | `app/database.py` | No explicit SQLite isolation mode or lock policy is exposed to API clients | Small |
| FR-4.1 | Implemented | `app/database.py::init_db` | Trigger prevents update/delete on ledger tables | — |
| FR-4.2 | Implemented | `app/models/ledger_entry.py`, `app/models/ledger_transaction.py` | Immutable ledger design is implemented | — |
| FR-4.3 | Implemented | `app/services/ledger_service.py::_append_ledger_entry` | Hash chain is used | — |
| FR-4.4 | Implemented | `app/services/ledger_service.py::reverse_transaction` | Reversal is compensating, not destructive | — |
| FR-4.5 | Implemented | `app/services/ledger_service.py::reverse_transaction` | Reversal is explicit and new transaction-based | — |
| FR-4.6 | Implemented | `app/services/ledger_service.py::reverse_transaction` | No direct ledger mutation occurs; reversal is compensating | — |
| FR-4.7 | Implemented | `app/services/ledger_service.py::reconcile` | Hash-chain verification is included in reconciliation | — |
| FR-4.8 | Implemented | `app/models/ledger_entry.py` | Append-only design is enforced by database triggers | — |
| FR-5.1 | Implemented | `app/api/routes/admin.py::reconciliation` | None observed | — |
| FR-5.2 | Implemented | `app/services/ledger_service.py::reconcile` | Reconciliation compares wallet balances with ledger totals | — |
| FR-5.3 | Implemented | `app/services/ledger_service.py::reconcile` | PASS/FAIL status is returned | — |
| FR-5.4 | Implemented | `app/services/ledger_service.py::reconcile` | Discrepancies include transaction and wallet mismatches | — |
| FR-5.5 | Implemented | `app/api/routes/admin.py` | Admin key enforcement is implemented | — |
| FR-5.6 | Implemented | `app/services/ledger_service.py::reconcile` | Hash-chain checks are included in reconciliation | — |
| FR-5.7 | Implemented | `app/services/ledger_service.py::reconcile` | Returns aggregated discrepancy list | — |
| NFR-001 | Partial | `app/database.py`, `app/services/ledger_service.py` | Core correctness exists, but not full production hardening | Medium |
| NFR-002 | Partial | `app/services/ledger_service.py::transfer`, `reconcile` | Correctness is present, but not broad enterprise-quality robustness | Medium |
| NFR-003 | Partial | `app/services/ledger_service.py` | Input validation exists, but not all production safety layers are present | Small |
| NFR-004 | Partial | `app/database.py` | WAL + foreign keys help safety, but no formal concurrency lock policy is implemented | Small |
| NFR-005 | Partial | `app/database.py`, `app/services/ledger_service.py` | Integrity rules exist, but not full audit/compliance controls | Medium |
| NFR-006 | Partial | `app/database.py` and `app/services/ledger_service.py` | Integrity logic is present but not full operational resilience | Medium |
| NFR-007 | Partial | `app/api/routes/admin.py` | Admin access is limited by key, but not full RBAC | Small |
| NFR-008 | Partial | `app/schemas/*` | Input validation exists, but there is no full security policy or exportable audit trail | Small |
| NFR-009 | Partial | `app/services/ledger_service.py` | Ledger rules exist, but not full compliance/reporting tooling | Medium |
| NFR-010 | Partial | `app/services/ledger_service.py` | Core logic is present, but full system reliability is not production-grade | Medium |
| NFR-011 | Partial | `app/database.py` | SQLite WAL helps, but no production-grade durability/HA design is present | Medium |
| NFR-012 | Partial | `app/services/ledger_service.py` | Some operational safeguards are present, but no full instrumentation | Medium |
| NFR-013 | Partial | `app/api/routes/*` and `app/schemas/*` | API behavior is structured but not full enterprise API governance | Small |
| NFR-014 | Partial | `app/services/ledger_service.py` | Core nonfunctional correctness is present, but not full bank-style ops quality | Medium |
| NFR-015 | Partial | `app/services/ledger_service.py`, `app/models/ledger_entry.py` | Some requirements are met, but not full audit reporting or data retention policy | Medium |
| NFR-016 | Partial | `app/api/routes/admin.py` | Basic admin reconciliation exists, but not full governance surface | Small |
| NFR-017 | Partial | `app/services/ledger_service.py` | Ledger correctness is implemented, but not full legal/regulatory controls | Medium |
| NFR-018 | Partial | `app/database.py` | Trigger-based immutability exists, but not full forensic retention policy | Medium |
| NFR-019 | Partial | `app/services/ledger_service.py` | Some business-level safety is present, but not a full banking-grade production environment | Medium |
| NFR-020 | Partial | `app/database.py` and `app/services/ledger_service.py` | Good local correctness, but not high-scale production concurrency | Medium |
| NFR-021 | Not implemented | — | No real payment integration, bank settlement, or external financial rail | Large |
| NFR-022 | Not implemented | — | No dashboard/UI or customer portal | Medium |
| NFR-023 | Not implemented | — | No per-user auth or role hierarchy beyond admin key | Large |
| NFR-024 | Not implemented | — | No distributed locking, distributed database, or cluster architecture | Large |
| NFR-025 | Not implemented | — | No notifications/webhooks/real-time external integrations | Medium |
| NFR-026 | Not implemented | — | No FX/exchange engine or multi-currency cross-border settlement | Large |
| BR-1 | Implemented | `app/models/wallet.py`, `app/services/ledger_service.py` | None observed | — |
| BR-2 | Implemented | `app/services/ledger_service.py::deposit` | Deposit directly updates a wallet balance, not a system-funding account balance | Small |
| BR-3 | Partial | `app/services/ledger_service.py::transfer` | Same-currency and sufficient-funds rules are enforced; system-funding-account semantics are not modeled | Small |
| BR-4 | Implemented | `app/services/ledger_service.py::reconcile` | None observed | — |
| BR-5 | Implemented | `app/database.py` trigger logic | Immutable ledger entries are enforced | — |
| BR-6 | Implemented | `app/services/ledger_service.py::reverse_transaction` | Reversal is implemented as explicit compensating transaction | — |
| BR-7 | Partial | `app/services/ledger_service.py::transfer` | Idempotency exists, but in request body rather than required header | Small |
| BR-8 | Partial | `app/api/routes/admin.py` | Admin reconciliation requires key, but there is no broader admin governance model | Small |
| SK-1 | Not implemented | — | No agent skill files or skills workflow in codebase | Large |
| SK-2 | Not implemented | — | No agent-skill functionality is implemented | Large |
| SK-3 | Not implemented | — | No local-check / brain-ingest / brain-query workflow in repository | Large |
| SK-4 | Not implemented | — | No skill execution interface present | Large |
| SK-5 | Not implemented | — | No agent lifecycle or skill registry is present | Large |
| SK-6 | Not implemented | — | No workflow automation for AI-assisted SDLC features | Large |
| TQ-1 | Partial | `tests/test_basic_wallet_flow.py`, `tests/test_reversal_flow.py` | Unit-like coverage exists, but not a full accounting test suite | Small |
| TQ-2 | Not implemented | — | No database transaction rollback test found in `tests/` | Small |
| TQ-3 | Partial | `tests/test_basic_wallet_flow.py` and `tests/test_reversal_flow.py` | Some end-to-end behavior is covered, but not complete FR coverage | Small |
| TQ-4 | Partial | `tests/test_wallet_validation.py` | Negative validation tests exist, but not comprehensive | Small |
| TQ-5 | Not implemented | — | No isolated CI database or CI harness is present in codebase | Medium |
| TQ-6 | Implemented | `app/schemas/transaction.py`, `app/models/wallet.py`, `app/models/ledger_entry.py` | Amounts are integer `int`/`Integer`, not float | — |
| TQ-7 | Partial | `tests/test_wallet_entries_and_admin.py` | Security/authorization checks exist, but no broader security test suite | Small |
| TQ-8 | Not implemented | — | No concurrency stress race test found in `tests/` | Small |

## A. Deposits

- One deposit writes:
  - 1 `LedgerTransaction` row
  - 1 `LedgerEntry` row
- There is no system funding account in the current implementation.
  - `app/services/ledger_service.py::deposit` directly updates `wallet.balance_minor` and then creates a ledger entry.
- The sum of all balances in a currency can be non-zero in the current code.
  - The code does not implement a global invariant equivalent to “sum of all wallet balances for USD must equal the system funding account balance” or a global ledger balancing rule across all wallets.

## B. Concurrency

- `BEGIN IMMEDIATE` is not used in the current code.
- SQLite transaction mode is set in `app/database.py` by executing PRAGMAs:
  - `PRAGMA journal_mode=WAL;`
  - `PRAGMA synchronous=NORMAL;`
  - `PRAGMA busy_timeout = 5000;`
  - `PRAGMA foreign_keys = ON;`
- This is configured on the SQLAlchemy engine through `create_engine(...)` and `engine.begin()`.
- There is no 503/Retry-After implementation in the API layer.
  - no API returns `503` with a `Retry-After` header
  - no explicit lock retry logic or HTTP retry policy is present

## C. Idempotency-Key behavior

- The API does not require an HTTP `Idempotency-Key` header.
- The current implementation expects `idempotency_key` as a JSON field in request bodies.
- Missing key does not return a custom 400; it fails as a validation error (typically `422`) from Pydantic.
- A failed request is prevented from leaving an idempotency record in the normal validation path because the record is inserted only after successful processing in `LedgerService.transfer()` and `LedgerService.reverse_transaction()`.

## D. Float handling

- No float is used for monetary amounts in the checked code.
- `amount_minor` is an integer in `app/schemas/transaction.py`
- `wallet.balance_minor` is an integer in `app/models/wallet.py`
- `ledger_entry.amount_minor` is an integer in `app/models/ledger_entry.py`
- `ledger_transaction.amount_minor` is an integer in `app/models/ledger_transaction.py`
- No float-based JSON parsing for money is present in the code paths reviewed.

## E. SRS items not needed by the project statement, and difficult/ambiguous items

### Not needed by the project statement
- real payment gateway integration
- external bank or settlement integration
- UI / frontend / customer portal
- multi-node or distributed database architecture
- per-user authentication / login flow
- exchange-rate or FX engine
- notifications, webhooks, push/email systems
- agent-skill workflow files (`SK-*` items)

### Hard, ambiguous, or contradictory to implement
- system funding account wording vs current code
- idempotency key as header vs JSON body field
- concurrency requirement vs WAL + busy timeout without `BEGIN IMMEDIATE`
- no explicit 503 + Retry-After semantics
- some NFR and SK items are outside the actual project scope and are not required to demonstrate the essential solution

## F. Extra implementation not asked by the SRS

The following are minor extras not central to the SRS problem statement:
- `is_system` flag on wallets
- simple cursor-based wallet-entry pagination
- extra metadata fields such as `created_at`

These are not major deviations but they are not central requirements of the original statement either.

## G. Test file coverage and concurrency/rollback/precision status

### `tests/test_basic_wallet_flow.py`
Covers:
- FR-1.x: user and wallet creation
- FR-2.x: transfer success and replayed transfer
- FR-5.x: admin reconciliation smoke check

Concurrency test: No
Rollback test: No
Precision test: No

### `tests/test_reversal_flow.py`
Covers:
- FR-4.x: reversal behavior
- FR-2.x: transfer before reversal

Concurrency test: No
Rollback test: No
Precision test: No

### `tests/test_wallet_validation.py`
Covers:
- validation failures for transfers and deposits
- invalid amount and invalid payload handling

Concurrency test: No
Rollback test: No
Precision test: No

### `tests/test_wallet_entries_and_admin.py`
Covers:
- FR-4.x: wallet entries are returned
- FR-5.x: admin key enforcement and reconciliation route validation

Concurrency test: No
Rollback test: No
Precision test: No

### Overall test gaps
- Concurrency test: No
- Rollback test: No
- Precision test: No

## Final factual assessment

The project implements the core ledger foundation and the central problem statement requirements:
- wallet creation
- deposit
- safe transfer
- idempotent replay protection
- reversal
- reconciliation
- immutable ledger entries

However, it does not fully implement several broader SRS requirements, including explicit concurrency lock semantics, header-based idempotency, system funding account model, 503/Retry-After behavior, and the full set of testing/integration requirements described in the SRS.

The current implementation is a realistic, minimal but correct ledger backend for the project statement, not a full production financial platform.
