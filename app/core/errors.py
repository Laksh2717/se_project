class ApiError(Exception):
    """Base class for all expected API errors (rendered as the JSON error envelope)."""

    status_code = 400
    code = "VALIDATION_ERROR"

    def __init__(self, message: str, status_code: int | None = None, code: str | None = None, headers: dict | None = None):
        super().__init__(message)
        self.message = message
        if status_code is not None:
            self.status_code = status_code
        if code is not None:
            self.code = code
        self.headers = headers or {}


class ValidationError(ApiError):
    """Malformed input: 400."""

    status_code = 400
    code = "VALIDATION_ERROR"


class UnauthorizedError(ApiError):
    status_code = 401
    code = "UNAUTHORIZED"


class NotFoundError(ApiError):
    status_code = 404
    code = "NOT_FOUND"


class ConflictError(ApiError):
    status_code = 409
    code = "CONFLICT"


class UnprocessableError(ApiError):
    """Well-formed but semantically invalid request: 422 with a specific code."""

    status_code = 422

    def __init__(self, code: str, message: str):
        super().__init__(message, code=code)


class InsufficientFundsError(UnprocessableError):
    def __init__(self, message: str = "insufficient funds"):
        super().__init__("INSUFFICIENT_FUNDS", message)


class DatabaseBusyError(ApiError):
    status_code = 503
    code = "DATABASE_BUSY"

    def __init__(self, message: str = "database is busy, retry shortly"):
        super().__init__(message, headers={"Retry-After": "1"})
