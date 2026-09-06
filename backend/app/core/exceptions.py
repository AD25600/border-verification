from fastapi import Request, status
from fastapi.responses import JSONResponse


class AppError(Exception):
    def __init__(self, message: str, status_code: int = status.HTTP_400_BAD_REQUEST, code: str = "app_error"):
        self.message = message
        self.status_code = status_code
        self.code = code
        super().__init__(message)


class NotFoundError(AppError):
    def __init__(self, message: str = "Resource not found"):
        super().__init__(message, status_code=status.HTTP_404_NOT_FOUND, code="not_found")


class UnauthorizedError(AppError):
    def __init__(self, message: str = "Not authenticated"):
        super().__init__(message, status_code=status.HTTP_401_UNAUTHORIZED, code="unauthorized")


class ForbiddenError(AppError):
    def __init__(self, message: str = "Insufficient permissions"):
        super().__init__(message, status_code=status.HTTP_403_FORBIDDEN, code="forbidden")


class ConflictError(AppError):
    def __init__(self, message: str = "Resource already exists"):
        super().__init__(message, status_code=status.HTTP_409_CONFLICT, code="conflict")


class ValidationError(AppError):
    """Malformed or invalid input that the client can fix (e.g. bad file type)."""

    def __init__(self, message: str = "Invalid input"):
        super().__init__(message, status_code=status.HTTP_422_UNPROCESSABLE_ENTITY, code="validation_error")


class MLComponentNotConfiguredError(AppError):
    """
    Raised when a pipeline stage's adapter has not been wired to a real
    implementation yet (ADAPTER_CLASS setting left blank, or the scaffold stub is
    still in place). This must NEVER be silently swallowed into a fabricated
    result — it is surfaced to the caller as a clear, actionable 503.
    """

    def __init__(self, component: str, message: str | None = None):
        super().__init__(
            message or f"The '{component}' component has not been configured yet.",
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            code="ml_component_not_configured",
        )


class PipelineStageError(AppError):
    """
    Raised when a configured ML component runs but fails during inference
    (bad input, model error, timeout, etc). Distinct from
    MLComponentNotConfiguredError, which means nothing was wired up at all.
    """

    def __init__(self, stage: str, message: str):
        super().__init__(
            f"Pipeline stage '{stage}' failed: {message}",
            status_code=status.HTTP_502_BAD_GATEWAY,
            code="pipeline_stage_error",
        )


async def app_error_handler(request: Request, exc: AppError) -> JSONResponse:
    return JSONResponse(
        status_code=exc.status_code,
        content={"status": "error", "code": exc.code, "message": exc.message},
    )


async def unhandled_exception_handler(request: Request, exc: Exception) -> JSONResponse:
    return JSONResponse(
        status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
        content={"status": "error", "code": "internal_error", "message": "An unexpected error occurred."},
    )
