import re

from fastapi import Header, Request

from app.core.errors import ValidationError

_KEY_RE = re.compile(r"^[A-Za-z0-9_-]{1,64}$")


def get_write_db(request: Request):
    """Session whose transactions start with BEGIN IMMEDIATE (use for every state-changing endpoint)."""
    db = request.app.state.write_session_factory()
    try:
        yield db
    finally:
        db.close()


def get_read_db(request: Request):
    """Session whose transactions start with BEGIN DEFERRED (one consistent snapshot)."""
    db = request.app.state.read_session_factory()
    try:
        yield db
    finally:
        db.close()


def idempotency_key(key: str | None = Header(default=None, alias="Idempotency-Key")) -> str:
    if key is None or not _KEY_RE.fullmatch(key):
        raise ValidationError("Idempotency-Key header is required: 1 to 64 characters from A-Z a-z 0-9 _ -")
    return key
