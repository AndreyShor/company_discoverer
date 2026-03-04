from __future__ import annotations

import stripe

from core.config import settings

stripe.api_key = settings.stripe_secret_key

STRIPE_WEBHOOK_SECRET: str = settings.stripe_webhook_secret
