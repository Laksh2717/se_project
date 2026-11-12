import secrets

from fastapi import APIRouter, Depends, Header
from sqlalchemy.orm import Session

from app.api.deps import get_read_db
from app.config import get_settings
from app.core.errors import UnauthorizedError
from app.services.ledger_service import LedgerService

router = APIRouter(prefix="/v1", tags=["admin"])


@router.get("/admin/reconciliation", summary="Verify the whole ledger (admin only)")
def reconciliation(x_admin_key: str | None = Header(default=None, alias="X-Admin-Key"),
                   db: Session = Depends(get_read_db)):
    expected = get_settings().admin_api_key
    if x_admin_key is None or not secrets.compare_digest(x_admin_key.encode(), expected.encode()):
        raise UnauthorizedError("missing or invalid admin credential")
    return LedgerService(db).reconcile()
