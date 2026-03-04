"""Warm up the OpenAI embedding model by sending a single test embedding request."""
from __future__ import annotations

import asyncio

from openai import AsyncOpenAI

from core.config import settings


async def warmup() -> None:
    client = AsyncOpenAI(api_key=settings.openai_api_key)
    response = await client.embeddings.create(
        model="text-embedding-3-small",
        input="warmup",
    )
    dimensions = len(response.data[0].embedding)
    print(f"Model warmed up. Embedding dimensions: {dimensions}")


if __name__ == "__main__":
    asyncio.run(warmup())
