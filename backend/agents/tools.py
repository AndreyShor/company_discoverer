"""
tools.py – LangChain @tool wrappers for the Company Intelligence Agent.

Each tool is an async function decorated with @tool so LangGraph's ToolNode
can call them automatically when the research LLM emits a tool-call.
"""

from __future__ import annotations
import asyncio
import time
import json
from typing import Optional

import httpx
from bs4 import BeautifulSoup
from ddgs import DDGS
from langchain_core.tools import tool


# ────────────────────────────────────────────────────────────────────────────
# DuckDuckGo Search Tool
# ────────────────────────────────────────────────────────────────────────────

@tool
async def ddgs_search_tool(query: str, max_results: int = 5) -> str:
    """
    Search DuckDuckGo for public information about a company.

    Use targeted queries such as:
    - "<company> <country> business overview"
    - "<company> <country> recent news 2024"
    - "<company> annual report financials"

    Returns a JSON string: list of {"title", "href", "body"} dicts.
    """
    def _search_sync(q: str, n: int):
        time.sleep(0.5)  # light rate-limit guard
        ddgs = DDGS()
        return ddgs.text(q, max_results=n)

    try:
        raw = await asyncio.to_thread(_search_sync, query, max_results)
        results = [
            {"title": r.get("title", ""), "href": r.get("href", ""), "body": r.get("body", "")}
            for r in (raw or [])
        ]
        return json.dumps(results, ensure_ascii=False)
    except Exception as e:
        return json.dumps({"error": str(e)})


# ────────────────────────────────────────────────────────────────────────────
# Web Page Scraper Tool
# ────────────────────────────────────────────────────────────────────────────

@tool
async def page_scrape_tool(url: str, max_chars: int = 4000) -> str:
    """
    Fetch a web page and return its plain-text content (stripped of HTML).

    Use this on URLs returned by ddgs_search_tool to get the full article or
    page content rather than a short snippet.

    Returns the extracted text, truncated to max_chars if too long.
    """
    try:
        headers = {
            "User-Agent": (
                "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) "
                "AppleWebKit/537.36 (KHTML, like Gecko) "
                "Chrome/120.0.0.0 Safari/537.36"
            )
        }
        async with httpx.AsyncClient(
            timeout=15,
            follow_redirects=True,
            headers=headers,
        ) as client:
            resp = await client.get(url)
            resp.raise_for_status()

        soup = BeautifulSoup(resp.text, "html.parser")
        for tag in soup(["script", "style", "nav", "footer", "header", "aside"]):
            tag.decompose()

        text = soup.get_text(separator=" ", strip=True)
        if len(text) > max_chars:
            text = text[:max_chars] + "\n\n[TRUNCATED]"
        return text if text else "No readable content found."
    except Exception as e:
        return f"Scraping failed for {url}: {e}"
