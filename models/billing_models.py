from __future__ import annotations

from enum import StrEnum

from pydantic import BaseModel, Field, PositiveInt


class PlanTier(StrEnum):
    FREE = "free"
    PRO = "pro"
    ENTERPRISE = "enterprise"


class CheckoutSessionRequest(BaseModel):
    plan: PlanTier
    success_url: str
    cancel_url: str


class CheckoutSessionResponse(BaseModel):
    session_id: str
    checkout_url: str


class SubscriptionStatus(BaseModel):
    plan: PlanTier
    status: str
    current_period_end: int


class WebhookEvent(BaseModel):
    """Raw Stripe webhook event envelope – body is passed through as-is."""

    type: str
    data: dict
