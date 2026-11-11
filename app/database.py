from sqlalchemy import create_engine, text
from sqlalchemy.orm import declarative_base, sessionmaker

from app.config import get_settings

settings = get_settings()
engine = create_engine(
    settings.database_url,
    connect_args={"check_same_thread": False, "timeout": 30},
    pool_pre_ping=True,
)
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
Base = declarative_base()


def configure_sqlite() -> None:
    with engine.begin() as conn:
        conn.execute(text("PRAGMA journal_mode=WAL;"))
        conn.execute(text("PRAGMA synchronous=NORMAL;"))
        conn.execute(text("PRAGMA busy_timeout = 5000;"))
        conn.execute(text("PRAGMA foreign_keys = ON;"))


configure_sqlite()


def init_db() -> None:
    from app.models import User, Wallet, LedgerTransaction, LedgerEntry, IdempotencyKey  # noqa: F401
    Base.metadata.create_all(bind=engine)

    with engine.begin() as conn:
        conn.execute(text("""
            CREATE TRIGGER IF NOT EXISTS prevent_update_ledger_transactions
            BEFORE UPDATE ON ledger_transactions
            BEGIN
                SELECT RAISE(ABORT, 'ledger_transactions are immutable');
            END;
        """))
        conn.execute(text("""
            CREATE TRIGGER IF NOT EXISTS prevent_delete_ledger_transactions
            BEFORE DELETE ON ledger_transactions
            BEGIN
                SELECT RAISE(ABORT, 'ledger_transactions are immutable');
            END;
        """))
        conn.execute(text("""
            CREATE TRIGGER IF NOT EXISTS prevent_update_ledger_entries
            BEFORE UPDATE ON ledger_entries
            BEGIN
                SELECT RAISE(ABORT, 'ledger_entries are immutable');
            END;
        """))
        conn.execute(text("""
            CREATE TRIGGER IF NOT EXISTS prevent_delete_ledger_entries
            BEFORE DELETE ON ledger_entries
            BEGIN
                SELECT RAISE(ABORT, 'ledger_entries are immutable');
            END;
        """))


def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()
