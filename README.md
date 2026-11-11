# Financial Ledger & Digital Wallet API

This project implements a financial ledger and digital wallet API based on the SRS document in this repository.

## Stack

- Python 3.11+
- FastAPI
- SQLAlchemy
- SQLite
- pytest

## Setup

1. Create a virtual environment.
2. Install dependencies:
   ```bash
   pip install -r requirements.txt
   ```
3. Copy `.env.example` to `.env` and adjust values.
4. Run the app:
   ```bash
   uvicorn app.main:app --reload
   ```

## Endpoints

- `GET /v1/health`
- `POST /v1/wallets`
- `GET /v1/wallets/{wallet_id}`

## Notes

This is the initial scaffold for the SRS-driven implementation.
