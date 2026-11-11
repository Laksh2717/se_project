from fastapi import FastAPI, Request
from fastapi.exceptions import RequestValidationError
from fastapi.responses import JSONResponse

from app.api.routes.admin import router as admin_router
from app.api.routes.health import router as health_router
from app.api.routes.reversals import router as reversals_router
from app.api.routes.transactions import router as transactions_router
from app.api.routes.users import router as users_router
from app.api.routes.wallets import router as wallets_router
from app.api.routes.wallet_entries import router as wallet_entries_router
from app.config import get_settings
from app.core.errors import ApiError
from app.database import init_db

settings = get_settings()

app = FastAPI(
    title=settings.app_name,
    version=settings.app_version,
    description="Financial Ledger and Digital Wallet API",
)

init_db()

app.include_router(health_router)
app.include_router(wallets_router)
app.include_router(admin_router)
app.include_router(users_router)
app.include_router(transactions_router)
app.include_router(reversals_router)
app.include_router(wallet_entries_router)


@app.exception_handler(ApiError)
async def api_error_handler(request: Request, exc: ApiError):
    return JSONResponse(status_code=exc.status_code, content={"detail": exc.message})


@app.exception_handler(RequestValidationError)
async def validation_error_handler(request: Request, exc: RequestValidationError):
    return JSONResponse(status_code=422, content={"detail": exc.errors()})


@app.get("/")
def root():
    return {"message": "Financial Ledger API is running"}
