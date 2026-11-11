from fastapi import APIRouter, Depends, Header, HTTPException
from sqlalchemy.orm import Session

from app.config import get_settings
from app.database import get_db
from app.services.ledger_service import LedgerService

settings = get_settings()
router = APIRouter(prefix="/v1", tags=["admin"])


@router.get("/admin/reconciliation")
def reconciliation(
    x_admin_key: str | None = Header(default=None, alias="X-Admin-Key"),
    db: Session = Depends(get_db),
):
    if x_admin_key != settings.admin_api_key:
        raise HTTPException(status_code=401, detail="Unauthorized")

    service = LedgerService(db)
    return service.reconcile()
