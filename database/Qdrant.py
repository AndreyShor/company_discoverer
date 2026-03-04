from __future__ import annotations

from typing import Optional

from qdrant_client import AsyncQdrantClient
from qdrant_client.http.models import Distance, VectorParams
from tenacity import retry, stop_after_attempt, wait_exponential

from core.config import settings
from core.logging import get_logger

logger = get_logger(__name__)

COLLECTION_COMPANY_PROFILES = "company_profiles"
VECTOR_SIZE = 1536  # OpenAI text-embedding-3-small

_qdrant_client: Optional[AsyncQdrantClient] = None


def get_qdrant() -> AsyncQdrantClient:
    """Return the shared Qdrant async client instance."""
    if _qdrant_client is None:
        raise RuntimeError("Qdrant client has not been initialised. Call init_qdrant() first.")
    return _qdrant_client


@retry(stop=stop_after_attempt(5), wait=wait_exponential(multiplier=1, min=1, max=10))
async def init_qdrant() -> AsyncQdrantClient:
    """Create the global Qdrant client and ensure required collections exist."""
    global _qdrant_client

    kwargs: dict = {"url": settings.qdrant_url}
    if settings.qdrant_api_key:
        kwargs["api_key"] = settings.qdrant_api_key

    client = AsyncQdrantClient(**kwargs)
    await _ensure_collections(client)
    _qdrant_client = client
    logger.info("qdrant_connected", url=settings.qdrant_url)
    return client


async def _ensure_collections(client: AsyncQdrantClient) -> None:
    """Create Qdrant collections if they do not already exist."""
    existing = {c.name for c in (await client.get_collections()).collections}

    if COLLECTION_COMPANY_PROFILES not in existing:
        await client.create_collection(
            collection_name=COLLECTION_COMPANY_PROFILES,
            vectors_config=VectorParams(size=VECTOR_SIZE, distance=Distance.COSINE),
        )
        logger.info("qdrant_collection_created", collection=COLLECTION_COMPANY_PROFILES)


async def close_qdrant() -> None:
    """Close the Qdrant connection."""
    global _qdrant_client
    if _qdrant_client is not None:
        await _qdrant_client.close()
        _qdrant_client = None
