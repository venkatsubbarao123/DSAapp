"""Centralized error handling and standardized exception responses."""

from fastapi import FastAPI, Request, status
from fastapi.exceptions import RequestValidationError
from starlette.exceptions import HTTPException as StarletteHTTPException
from starlette.responses import JSONResponse

from backend.app.core.logging import logger, request_id_ctx


def get_request_id(request: Request) -> str:
    """Safely extracts request_id from request state or context variable."""
    return (
        getattr(request.state, "request_id", None) or request_id_ctx.get() or "unknown"
    )


def register_error_handlers(app: FastAPI) -> None:
    """Registers global exception handlers enforcing uniform API error envelopes."""

    @app.exception_handler(StarletteHTTPException)
    async def http_exception_handler(
        request: Request, exc: StarletteHTTPException
    ) -> JSONResponse:
        req_id = get_request_id(request)
        error_code = f"HTTP_{exc.status_code}"

        # Determine code based on common status codes
        if exc.status_code == status.HTTP_404_NOT_FOUND:
            error_code = "NOT_FOUND"
        elif exc.status_code == status.HTTP_401_UNAUTHORIZED:
            error_code = "UNAUTHORIZED"
        elif exc.status_code == status.HTTP_403_FORBIDDEN:
            error_code = "FORBIDDEN"
        elif exc.status_code == status.HTTP_400_BAD_REQUEST:
            error_code = "BAD_REQUEST"

        message = (
            str(exc.detail)
            if isinstance(exc.detail, str)
            else "An HTTP error occurred."
        )

        return JSONResponse(
            status_code=exc.status_code,
            content={
                "success": False,
                "error": {
                    "code": error_code,
                    "message": message,
                    "request_id": req_id,
                },
            },
            headers={"X-Request-ID": req_id},
        )

    @app.exception_handler(RequestValidationError)
    async def validation_exception_handler(
        request: Request, exc: RequestValidationError
    ) -> JSONResponse:
        req_id = get_request_id(request)
        logger.warning(
            f"Validation failed for {request.method} {request.url.path}",
            extra={"request_id": req_id, "error_code": "VALIDATION_ERROR"},
        )

        # Sanitize validation error details to avoid raw stack/path leakage
        safe_errors = []
        for err in exc.errors():
            safe_errors.append(
                {
                    "field": " -> ".join(str(loc) for loc in err.get("loc", [])),
                    "issue": err.get("msg", "Invalid input"),
                }
            )

        return JSONResponse(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            content={
                "success": False,
                "error": {
                    "code": "VALIDATION_ERROR",
                    "message": "The submitted payload failed validation.",
                    "request_id": req_id,
                    "details": safe_errors,
                },
            },
            headers={"X-Request-ID": req_id},
        )

    @app.exception_handler(Exception)
    async def unhandled_exception_handler(
        request: Request, exc: Exception
    ) -> JSONResponse:
        req_id = get_request_id(request)
        # Log complete exception server-side for debugging
        logger.exception(
            f"Unhandled internal server error during {request.method} {request.url.path}: {exc!s}",
            extra={"request_id": req_id, "error_code": "INTERNAL_SERVER_ERROR"},
        )

        # Return sanitized message to client without exposing stack trace, paths, or internals
        return JSONResponse(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            content={
                "success": False,
                "error": {
                    "code": "INTERNAL_SERVER_ERROR",
                    "message": "An unexpected error occurred. Please contact support with the request ID.",
                    "request_id": req_id,
                },
            },
            headers={"X-Request-ID": req_id},
        )
