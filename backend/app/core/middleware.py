"""Security, correlation, and size-limiting middlewares."""

import re
import time
import uuid
from collections.abc import Callable

from starlette.middleware.base import BaseHTTPMiddleware
from starlette.requests import Request
from starlette.responses import JSONResponse, Response

from backend.app.core.config import settings
from backend.app.core.logging import logger, request_id_ctx

# Sanitization regex for client-supplied X-Request-ID: alphanumeric, hyphens, and underscores only, max length 64
SAFE_REQUEST_ID_REGEX = re.compile(r"^[a-zA-Z0-9_\-]{1,64}$")


class RequestCorrelationMiddleware(BaseHTTPMiddleware):
    """Ensures every request has a safe correlation ID for tracing and logging."""

    async def dispatch(self, request: Request, call_next: Callable) -> Response:
        client_request_id = request.headers.get("x-request-id", "").strip()

        # Validate incoming ID or generate a secure UUID4
        if client_request_id and SAFE_REQUEST_ID_REGEX.match(client_request_id):
            request_id = client_request_id
        else:
            request_id = str(uuid.uuid4())

        # Store in context variable for logging and downstream handlers
        token = request_id_ctx.set(request_id)
        request.state.request_id = request_id

        start_time = time.perf_counter()
        status_code = 500
        try:
            response = await call_next(request)
            status_code = response.status_code
        except Exception as exc:
            status_code = 500
            logger.exception(
                f"Unhandled exception during {request.method} {request.url.path}: {exc!s}",
                extra={"request_id": request_id, "error_code": "INTERNAL_SERVER_ERROR"},
            )
            response = JSONResponse(
                status_code=500,
                content={
                    "success": False,
                    "error": {
                        "code": "INTERNAL_SERVER_ERROR",
                        "message": "An unexpected error occurred. Please contact support with the request ID.",
                        "request_id": request_id,
                    },
                },
                headers={"X-Request-ID": request_id},
            )
        finally:
            duration_ms = round((time.perf_counter() - start_time) * 1000, 2)
            logger.info(
                f"{request.method} {request.url.path} -> {status_code} ({duration_ms}ms)",
                extra={
                    "http_method": request.method,
                    "path": request.url.path,
                    "status_code": status_code,
                    "duration_ms": duration_ms,
                },
            )
            request_id_ctx.reset(token)

        # Inject correlation header into the outgoing response
        response.headers["X-Request-ID"] = request_id
        return response


class SecurityHeadersMiddleware(BaseHTTPMiddleware):
    """Injects defensive HTTP security headers to protect against clickjacking, MIME-sniffing, and XSS."""

    async def dispatch(self, request: Request, call_next: Callable) -> Response:
        response = await call_next(request)

        # Security Headers
        response.headers["X-Content-Type-Options"] = "nosniff"
        response.headers["X-Frame-Options"] = "DENY"
        response.headers["Referrer-Policy"] = "strict-origin-when-cross-origin"
        response.headers["Permissions-Policy"] = (
            "geolocation=(), microphone=(), camera=()"
        )

        # Baseline Content-Security-Policy
        # Restricts frame ancestors, scripts, objects, and base URI
        response.headers["Content-Security-Policy"] = (
            "default-src 'self'; "
            "frame-ancestors 'none'; "
            "object-src 'none'; "
            "base-uri 'self'; "
            "script-src 'self'; "
            "style-src 'self' 'unsafe-inline';"
        )

        # Strict-Transport-Security: Only enable in production where HTTPS is actively terminated
        if settings.ENVIRONMENT == "production":
            response.headers["Strict-Transport-Security"] = (
                "max-age=31536000; includeSubDomains"
            )

        return response


class RequestSizeLimitMiddleware(BaseHTTPMiddleware):
    """Enforces request payload size limits to protect against memory exhaustion."""

    async def dispatch(self, request: Request, call_next: Callable) -> Response:
        content_length = request.headers.get("content-length")
        if content_length:
            try:
                length = int(content_length)
                if length > settings.MAX_REQUEST_SIZE_BYTES:
                    req_id = (
                        getattr(request.state, "request_id", None)
                        or request_id_ctx.get()
                    )
                    return JSONResponse(
                        status_code=413,
                        content={
                            "success": False,
                            "error": {
                                "code": "PAYLOAD_TOO_LARGE",
                                "message": f"Request body exceeds maximum allowed size of {settings.MAX_REQUEST_SIZE_BYTES} bytes.",
                                "request_id": req_id,
                            },
                        },
                        headers={"X-Request-ID": req_id} if req_id else {},
                    )
            except ValueError:
                pass

        return await call_next(request)
