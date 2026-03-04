from __future__ import annotations

import sentry_sdk
from sentry_sdk.integrations.fastapi import FastApiIntegration
from sentry_sdk.integrations.starlette import StarletteIntegration

from core.config import settings


def init_sentry() -> None:
    """Initialize Sentry with FastAPI integration for traces, profiles, and exceptions."""
    if not settings.sentry_dsn:
        return

    sentry_sdk.init(
        dsn=settings.sentry_dsn,
        integrations=[
            StarletteIntegration(transaction_style="endpoint"),
            FastApiIntegration(transaction_style="endpoint"),
        ],
        traces_sample_rate=1.0 if settings.app_env != "production" else 0.2,
        profiles_sample_rate=1.0 if settings.app_env != "production" else 0.1,
        environment=settings.app_env,
        send_default_pii=False,
    )
