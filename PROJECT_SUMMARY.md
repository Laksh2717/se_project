# Financial Ledger & Digital Wallet API - Project Summary

## 1. Project overview

This project implements a backend financial ledger and digital wallet API using Python, FastAPI, SQLAlchemy, and SQLite. The core objective is to ensure financial correctness, protect against duplicate execution, preserve an immutable audit trail, and provide reconciliation checks that verify the ledger matches wallet balances.

The project is intentionally scoped to a realistic local-development implementation rather than a full banking or enterprise payment platform.

## 2. File structure

```text
SE_PROJECT/
├── app/
│   ├── api/
│   │   ├── routes/
│   │   │   ├── admin.py
│   │   │   ├── health.py
│   │   │   ├── reversals.py
│   │   │   ├── transactions.py
│   │   │   ├── users.py
│   │   │   ├── wallets.py
│   │   │   └── wallet_entries.py
│   │   └── __init__.py
│   ├── config.py
│   ├── core/
│   │   ├── errors.py
│   │   └── __init__.py
│   ├── database.py
│   ├── main.py
│   ├── models/
│   │   ├── __init__.py
│   │   ├── idempotency_key.py
│   │   ├── ledger_entry.py
│   │   ├── ledger_transaction.py
│   │   ├── user.py
│   │   └── wallet.py
│   ├── schemas/
│   │   ├── __init__.py
│   │   ├── transaction.py
│   │   ├── user.py
│   │   └── wallet.py
│   └── services/
│       └── ledger_service.py
├── tests/
│   ├── test_basic_wallet_flow.py
│   ├── test_reversal_flow.py
│   ├── test_wallet_entries_and_admin.py
│   ├── test_wallet_validation.py
│   └── ...
├── .env.example
├── README.md
├── requirements.txt
├── pytest.ini
├── Project_2_Financial_Ledger.pdf
├── SRS.pdf
└── financial_ledger.db
```

## 3. Main implementation files and responsibilities

### `app/main.py`
- Starts the FastAPI application
- Registers all route modules
- Configures error handling for `ApiError` and validation errors
- Exposes a basic root endpoint

### `app/database.py`
- Creates the SQLite engine
- Enables WAL mode and foreign keys
- Initializes database tables
- Creates database triggers to prevent direct updating or deleting of ledger tables

### `app/config.py`
- Loads app configuration from environment settings
- Stores the admin API key and app metadata

### `app/models/`
Contains the core domain models:
- `user.py`: user entity
- `wallet.py`: wallet entity with balance
- `ledger_transaction.py`: financial transaction record
- `ledger_entry.py`: immutable ledger entries with hash chaining
- `idempotency_key.py`: storage for idempotency behavior

### `app/services/ledger_service.py`
This is the central business logic layer. It implements:
- deposit logic
- transfer logic
- idempotent request handling
- reversal logic
- reconciliation logic
- hash-chain verification

### `app/api/routes/`
These route files expose the endpoints:
- `users.py`: user creation
- `wallets.py`: wallet creation and wallet lookup
- `transactions.py`: deposit and transfer endpoints
- `reversals.py`: transaction reversal endpoint
- `wallet_entries.py`: wallet history and ledger read access
- `admin.py`: admin reconciliation route
- `health.py`: health-check route

## 4. Features implemented in code

The project implements the following features from the original SRS/problem statement:

### 4.1 Wallet creation
- Users can be created
- Wallets can be attached to a user
- Wallets are initialized with a balance of zero

Implemented in:
- `app/api/routes/users.py`
- `app/api/routes/wallets.py`
- `app/models/user.py`
- `app/models/wallet.py`

### 4.2 Deposit support
- Deposit endpoint accepts wallet ID, amount, and currency
- Validates amount > 0
- Updates wallet balance
- Creates a ledger transaction + ledger entry
- Uses database transaction safety

Implemented in:
- `app/api/routes/transactions.py`
- `app/services/ledger_service.py::deposit`

### 4.3 Transfer support
- Transfers money from one wallet to another
- Validates same-currency requirement
- Rejects self-transfer
- Rejects insufficient funds
- Uses atomic DB behavior
- Records both debit and credit ledger entries

Implemented in:
- `app/api/routes/transactions.py`
- `app/services/ledger_service.py::transfer`

### 4.4 Idempotency
- Each mutating request can carry an idempotency key
- The same key with same payload returns original response
- Same key with different payload is rejected as conflict

Implemented in:
- `app/models/idempotency_key.py`
- `app/services/ledger_service.py`
- `app/api/routes/transactions.py`
- `app/api/routes/reversals.py`

### 4.5 Reversal support
- Valid completed transactions can be reversed
- Reversal creates compensating ledger records
- Duplicate reversal attempts are blocked
- Reversal does not alter previously immutable ledger records

Implemented in:
- `app/api/routes/reversals.py`
- `app/services/ledger_service.py::reverse_transaction`

### 4.6 Immutable ledger trail
- Ledger transactions and ledger entries cannot be updated or deleted via SQL triggers
- This matches the requirement for tamper-evident records

Implemented in:
- `app/database.py`

### 4.7 Hash chain / tamper evidence
- Each entry calculates a SHA-256 hash using previous hash, transaction id, wallet id, direction, amount, currency, and timestamp
- This creates a chain that helps detect tampering

Implemented in:
- `app/services/ledger_service.py::_build_entry_hash`
- `app/services/ledger_service.py::_last_entry_hash`
- `app/models/ledger_entry.py`

### 4.8 Reconciliation
- Admin route validates X-Admin-Key
- Compares wallet balances to ledger-derived totals
- Checks transaction de/credit totals and hash-chain integrity
- Returns PASS/FAIL and discrepancies

Implemented in:
- `app/api/routes/admin.py`
- `app/services/ledger_service.py::reconcile`

### 4.9 Wallet history / ledger query
- Wallet entries can be fetched via wallet endpoint
- History is available for audit and review

Implemented in:
- `app/api/routes/wallet_entries.py`
- `app/services/ledger_service.py`

## 5. Features from the original SRS that are present in code

From the original SRS/problem description, the following points are implemented in the codebase:

- Wallet initialization and balance tracking
- Double-entry-like ledger records for credits and debits
- Transfer between wallets with validation
- Idempotent transfer protection
- Prevention of balance overwrite by logic + ledger model
- Immutable ledger entries
- Reversal as an explicit compensating transaction
- Administrative reconciliation check
- Hash-based tamper-evidence
- Local SQLite-based storage
- Test coverage for wallet flow and reversal flow

## 6. Features from the original SRS that are not implemented in code

The following items were in the original SRS/problem description or expected broader scope, but are not implemented in the current codebase:

### 6.1 Real payment gateway integration
- No external bank API
- No Stripe/PayPal/UPI or real payment settlement
- No external transfer rails

### 6.2 Multi-user enterprise dashboard / UI
- No frontend or admin dashboard
- No web interface for users
- No browser-based wallet portal

### 6.3 Distributed / multi-node system
- No microservices architecture
- No distributed locks
- No cluster coordination
- No multi-instance synchronization layer

### 6.4 Advanced banking features
- No interest calculation
- No scheduled transfers
- No recurring payments
- No card management
- No KYC or AML flows
- No loan or credit lifecycle

### 6.5 Advanced security and regulatory features
- No two-factor authentication
- No role-based access control beyond a simple admin key check
- No encryption at rest for sensitive data
- No audit log export and compliance reporting

### 6.6 Large-scale concurrency / high-volume production concerns
- No production load balancing
- No distributed tracing
- No rate limiting at scale
- No message queues
- No large-scale observability stack

### 6.7 External notification systems
- No email/SMS notifications
- No push notifications
- No webhook support

### 6.8 True multi-currency ledger arbitrage or FX conversion engine
- No exchange-rate logic
- No settlement across different currencies beyond a validation check against same-currency transfers

## 7. Scope explanation

The current implementation is a correct, small, and defendable financial ledger project. It addresses the core requirements of the SRS and the project statement:
- money integrity
- idempotent retries
- ledger auditing
- transaction safety
- reconciliation

But it deliberately does not implement the broader “large banking system” functions because those would go beyond the intended scope of the course project and would increase complexity without improving the core submission outcome.

## 8. Final assessment

The project is submission-ready in terms of its implemented functionality and demonstrates the core SRS requirements in a working codebase. It is best described as a realistic, minimal but correct financial ledger backend, not a full production banking platform.

This aligns with the actual requirement of the project: build a mathematically sound digital wallet system with ledger integrity, not a complete enterprise financial system.
