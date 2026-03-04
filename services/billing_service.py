from __future__ import annotations

import asyncio
from typing import Optional

import stripe

from core.config import settings
from core.logging import get_logger
from models.billing_models import PlanTier, SubscriptionStatus

logger = get_logger(__name__)

_PLAN_PRICE_IDS: dict[PlanTier, str] = {
    PlanTier.PRO: "price_pro_placeholder",
    PlanTier.ENTERPRISE: "price_enterprise_placeholder",
}


async def create_checkout_session(
    plan: PlanTier,
    user_email: str,
    success_url: str,
    cancel_url: str,
) -> tuple[str, str]:
    """Create a Stripe Checkout session and return (session_id, checkout_url)."""
    price_id = _PLAN_PRICE_IDS.get(plan)
    if price_id is None:
        raise ValueError(f"No Stripe price configured for plan: {plan}")

    session = await asyncio.to_thread(
        stripe.checkout.Session.create,
        mode="subscription",
        customer_email=user_email,
        line_items=[{"price": price_id, "quantity": 1}],
        success_url=success_url,
        cancel_url=cancel_url,
    )
    return session.id, session.url


async def handle_webhook(payload: bytes, sig_header: str) -> None:
    """Verify and process an incoming Stripe webhook event."""
    try:
        event = stripe.Webhook.construct_event(
            payload, sig_header, settings.stripe_webhook_secret
        )
    except stripe.error.SignatureVerificationError as exc:
        logger.warning("stripe_webhook_invalid_signature", error=str(exc))
        raise ValueError("Invalid Stripe signature") from exc

    event_type: str = event["type"]
    logger.info("stripe_webhook_received", event_type=event_type)

    if event_type == "customer.subscription.updated":
        await _handle_subscription_updated(event["data"]["object"])
    elif event_type == "customer.subscription.deleted":
        await _handle_subscription_deleted(event["data"]["object"])
    elif event_type == "invoice.payment_failed":
        await _handle_payment_failed(event["data"]["object"])


async def _handle_subscription_updated(subscription: dict) -> None:
    logger.info("subscription_updated", subscription_id=subscription.get("id"))


async def _handle_subscription_deleted(subscription: dict) -> None:
    logger.info("subscription_deleted", subscription_id=subscription.get("id"))


async def _handle_payment_failed(invoice: dict) -> None:
    logger.warning("payment_failed", invoice_id=invoice.get("id"))
