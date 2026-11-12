from fastapi import FastAPI, Request
from fastapi.exceptions import RequestValidationError
from fastapi.responses import JSONResponse
from sqlalchemy.exc import OperationalError

from app.api.routes.admin import router as admin_router
from app.api.routes.health import router as health_router
from app.api.routes.reversals import router as reversals_router
from app.api.routes.transactions import router as transactions_router
from app.api.routes.users import router as users_router
from app.api.routes.wallet_entries import router as wallet_entries_router
from app.api.routes.wallets import router as wallets_router
from app.config import get_settings
from app.core.errors import ApiError
from app.database import init_db, make_engine, make_session_factories


def _error(status: int, code: str, message: str, headers: dict | None = None, **extra) -> JSONResponse:
    return JSONResponse(status_code=status, content={"error": {"code": code, "message": message, **extra}}, headers=headers)


def create_app(database_url: str | None = None, busy_timeout_ms: int | None = None) -> FastAPI:
    settings = get_settings()
    app = FastAPI(title=settings.app_name, version=settings.app_version,
                  description="Financial Ledger and Digital Wallet API")

    engine = make_engine(database_url or settings.database_url, busy_timeout_ms or settings.sqlite_busy_timeout_ms)
    init_db(engine)
    app.state.engine = engine
    app.state.write_session_factory, app.state.read_session_factory = make_session_factories(engine)

    for router in (health_router, users_router, wallets_router, transactions_router,
                   reversals_router, wallet_entries_router, admin_router):
        app.include_router(router)

    @app.exception_handler(ApiError)
    async def api_error_handler(request: Request, exc: ApiError):
        return _error(exc.status_code, exc.code, exc.message, exc.headers)

    @app.exception_handler(RequestValidationError)
    async def validation_handler(request: Request, exc: RequestValidationError):
        details = [{"field": ".".join(str(p) for p in e["loc"]), "message": e["msg"]} for e in exc.errors()]
        return _error(400, "VALIDATION_ERROR", "invalid request", details=details)

    @app.exception_handler(OperationalError)
    async def db_error_handler(request: Request, exc: OperationalError):
        if "locked" in str(exc.orig).lower() or "busy" in str(exc.orig).lower():
            return _error(503, "DATABASE_BUSY", "database is busy, retry shortly", {"Retry-After": "1"})
        return _error(500, "INTERNAL_ERROR", "internal server error")

    @app.exception_handler(Exception)
    async def unexpected_handler(request: Request, exc: Exception):
        return _error(500, "INTERNAL_ERROR", "internal server error")  # never leak stack traces, SQL or paths

    return app


app = create_app()
