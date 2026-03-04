from __future__ import annotations

import re
from typing import Callable

from fastapi import Request, Response
from fastapi.responses import JSONResponse
from starlette.middleware.base import BaseHTTPMiddleware
from starlette.types import ASGIApp


_XSS_PATTERNS: list[re.Pattern[str]] = [
    re.compile(r"<\s*script", re.IGNORECASE),
    re.compile(r"javascript\s*:", re.IGNORECASE),
    re.compile(r"on\w+\s*=", re.IGNORECASE),
]

_MAX_BODY_SCAN_BYTES = 64 * 1024  # 64 KB


class RequestXSSGuardMiddleware(BaseHTTPMiddleware):
    """Scans incoming request bodies for common XSS payloads and rejects them."""

    def __init__(self, app: ASGIApp) -> None:
        super().__init__(app)

    async def dispatch(self, request: Request, call_next: Callable) -> Response:
        content_type = request.headers.get("content-type", "")
        if request.method in ("POST", "PUT", "PATCH") and (
            "application/json" in content_type or "application/x-www-form-urlencoded" in content_type
        ):
            body = await request.body()
            sample = body[:_MAX_BODY_SCAN_BYTES].decode("utf-8", errors="replace")
            for pattern in _XSS_PATTERNS:
                if pattern.search(sample):
                    return JSONResponse(
                        status_code=400,
                        content={"detail": "Request body contains disallowed content."},
                    )
        return await call_next(request)


class SecurityHeadersMiddleware(BaseHTTPMiddleware):
    """Adds standard security response headers to every HTTP response."""

    _HEADERS: dict[str, str] = {
        "X-Content-Type-Options": "nosniff",
        "X-Frame-Options": "DENY",
        "X-XSS-Protection": "1; mode=block",
        "Strict-Transport-Security": "max-age=63072000; includeSubDomains; preload",
        "Referrer-Policy": "strict-origin-when-cross-origin",
        "Permissions-Policy": "geolocation=(), microphone=(), camera=()",
        "Content-Security-Policy": (
            "default-src 'self'; "
            "script-src 'self'; "
            "style-src 'self' 'unsafe-inline'; "
            "img-src 'self' data:; "
            "connect-src 'self'; "
            "frame-ancestors 'none';"
        ),
    }

    async def dispatch(self, request: Request, call_next: Callable) -> Response:
        response = await call_next(request)
        for header, value in self._HEADERS.items():
            response.headers[header] = value
        return response
