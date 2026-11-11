class ApiError(Exception):
    def __init__(self, message: str, status_code: int = 400):
        self.message = message
        self.status_code = status_code


class ValidationError(ApiError):
    def __init__(self, message: str):
        super().__init__(message, 422)


class NotFoundError(ApiError):
    def __init__(self, message: str):
        super().__init__(message, 404)


class ConflictError(ApiError):
    def __init__(self, message: str):
        super().__init__(message, 409)


class InsufficientFundsError(ApiError):
    def __init__(self, message: str):
        super().__init__(message, 422)
