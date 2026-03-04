from __future__ import annotations

from fastapi import APIRouter, Header, HTTPException, Request, status

import stripe as stripe_lib

from core.logging import get_logger
from models.billing_models import CheckoutSessionRequest, CheckoutSessionResponse
from services import billing_service

logger = get_logger(__name__)

router = APIRouter(prefix="/billing", tags=["billing"])


@router.post("/checkout", response_model=CheckoutSessionResponse, status_code=status.HTTP_201_CREATED)
async def create_checkout(body: CheckoutSessionRequest) -> CheckoutSessionResponse:
    """Create a Stripe checkout session for a subscription plan."""
    try:
        session_id, checkout_url = await billing_service.create_checkout_session(
            plan=body.plan,
            user_email="placeholder@example.com",
            success_url=body.success_url,
            cancel_url=body.cancel_url,
        )
    except ValueError as exc:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(exc)) from exc

    return CheckoutSessionResponse(session_id=session_id, checkout_url=checkout_url)


@router.post("/webhook", status_code=status.HTTP_200_OK)
async def stripe_webhook(
    request: Request,
    stripe_signature: str = Header(alias="stripe-signature"),
) -> dict:
    """Handle incoming Stripe webhook events."""
    payload = await request.body()
    try:
        await billing_service.handle_webhook(payload, stripe_signature)
    except ValueError as exc:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(exc)) from exc

    return {"received": True}
