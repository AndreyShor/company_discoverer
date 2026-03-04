"""Supabase RPC helpers for user-related queries."""
from __future__ import annotations

from supabase import AsyncClient


async def get_user_by_email(client: AsyncClient, email: str) -> dict | None:
    """Fetch a user record by email address."""
    result = await client.table("users").select("*").eq("email", email).maybe_single().execute()
    return result.data


async def create_user(client: AsyncClient, email: str, hashed_password: str) -> dict:
    """Insert a new user record and return the created row."""
    result = (
        await client.table("users")
        .insert({"email": email, "hashed_password": hashed_password})
        .execute()
    )
    return result.data[0]
