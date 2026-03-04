"""
CompanyIntelligenceAgent — LangGraph-based company research agent.

Architecture with PARALLEL specialist nodes:

  START
    │
    ▼
  _router_node           ── validates + seeds the initial message context
    │
    ├── REJECT ──────────► END
    │
    └── PROCEED ──────────────────────────────────────────┐
                                                          │
         ┌────────────────────────────────────────────────┘
         │  (parallel fan-out — all three start simultaneously)
         ├──► _financial_node   ──┐
         ├──► _market_node      ──┤► _report_node ──► END
         └──► _product_node     ──┘

Each specialist node:
  1. Runs targeted DuckDuckGo searches via ddgs_search_tool (async, threaded)
  2. Scrapes top URLs via page_scrape_tool
  3. Uses OpenAIConnector.ainvoke_structured to emit a typed Pydantic sub-model

_report_node:
  Receives all three sub-models from AgentState and calls ainvoke_structured
  to compose the final StructuredBusinessAnalysis.
"""

from __future__ import annotations

import asyncio
import json
from typing import Annotated, Any, Dict, List, Literal, Optional, TypedDict

from langchain_core.messages import AIMessage, HumanMessage, SystemMessage, BaseMessage
from langchain_core.runnables import RunnableConfig
from langgraph.graph import END, START, StateGraph
from langgraph.graph.message import add_messages

from agents.OpenAIConnector import OpenAIConnector
from agents.tools import ddgs_search_tool, page_scrape_tool
from models import (
    FinancialAnalysis,
    MarketPositioning,
    ProductAnalysis,
    StructuredBusinessAnalysis,
)


# ────────────────────────────────────────────────────────────────────────────
# Prompts
# ────────────────────────────────────────────────────────────────────────────

SYSTEM_PROMPT = """\
You are a professional business intelligence analyst AI.
Your job is to research a target company and extract accurate, source-backed information.
Only state what the retrieved sources actually say. Do not fabricate information.
If data is unavailable, acknowledge it explicitly.
"""

ROUTER_PROMPT = """\
You are validating an incoming company intelligence request.
Given a company name and a region, respond with JSON only:
  {"valid": true|false, "reason": "..."}
Return valid=true if both fields are non-empty and look like real company / region names.
Return valid=false (with a short reason) only for obviously nonsensical inputs.
"""

# ─── Financial ───────────────────────────────────────────────────────────────
FINANCIAL_SYSTEM = """\
You are a Financial Analysis specialist.
Your task: gather and summarise financial intelligence for the target company.
Focus on: revenue, funding history, valuation, profitability indicators, and key financial KPIs.
Use only information actually retrieved from sources. Do not guess numbers.
"""

# ─── Market Positioning ──────────────────────────────────────────────────────
MARKET_SYSTEM = """\
You are a Market Positioning specialist.
Your task: analyse the company's competitive landscape, geographic presence, target customers,
strategic differentiators, and recent strategic moves (acquisitions, partnerships, pivots).
Base everything on retrieved information only.
"""

# ─── Product ─────────────────────────────────────────────────────────────────
PRODUCT_SYSTEM = """\
You are a Product Intelligence specialist.
Your task: identify the company's core products & services, technology stack, pricing / monetisation model,
and notable recent product launches or features.
Base everything on retrieved information only.
"""

# ─── Final report ────────────────────────────────────────────────────────────
REPORT_SYSTEM = """\
You are assembling a final intelligence report from three specialist analyses.
Combine the financial, market-positioning, and product intelligence you have received into a
cohesive, executive-grade structured business analysis.
Write a 2-3 paragraph overview that integrates all three domains.
List key executives you encountered during research.
Deduplicate and list all sources referenced across all analyses.
"""


# ────────────────────────────────────────────────────────────────────────────
# State
# ────────────────────────────────────────────────────────────────────────────

class AgentState(TypedDict, total=False):
    """Shared state flowing through every graph node."""
    # Standard LangGraph message log (used for context & debugging)
    messages: Annotated[List[BaseMessage], add_messages]

    # Input
    company_name: str
    company_region: str

    # Routing
    is_valid_request: bool
    rejection_reason: Optional[str]

    # Specialist sub-reports (populated in parallel, read by _report_node)
    financial_analysis: Optional[FinancialAnalysis]
    market_positioning: Optional[MarketPositioning]
    product_analysis:   Optional[ProductAnalysis]

    # Final output
    structured_report: Optional[StructuredBusinessAnalysis]


# ────────────────────────────────────────────────────────────────────────────
# Helpers
# ────────────────────────────────────────────────────────────────────────────

async def _search_and_scrape(queries: List[str], max_results: int = 4, max_pages: int = 3) -> str:
    """
    Utility shared by all specialist nodes.
    Runs all search queries in parallel, then concurrently scrapes the top URLs.
    Returns a single concatenated context string.
    """
    # 1. Parallel searches
    search_tasks = [ddgs_search_tool.ainvoke({"query": q, "max_results": max_results}) for q in queries]
    raw_results = await asyncio.gather(*search_tasks, return_exceptions=True)

    # 2. Collect links & snippets
    all_items: List[Dict[str, str]] = []
    seen_urls: set = set()
    for raw in raw_results:
        if isinstance(raw, Exception):
            continue
        try:
            items = json.loads(raw) if isinstance(raw, str) else raw
            for item in (items if isinstance(items, list) else []):
                url = item.get("href", "")
                if url and url not in seen_urls:
                    seen_urls.add(url)
                    all_items.append(item)
        except Exception:
            pass

    # 3. Parallel scraping of top N pages
    urls_to_scrape = [item["href"] for item in all_items[:max_pages] if item.get("href")]
    scrape_tasks = [page_scrape_tool.ainvoke({"url": u}) for u in urls_to_scrape]
    scraped = await asyncio.gather(*scrape_tasks, return_exceptions=True)

    # 4. Build context string
    parts: List[str] = []
    for item in all_items:
        parts.append(f"Title: {item.get('title','')}\nURL: {item.get('href','')}\nSnippet: {item.get('body','')}")

    for url, text in zip(urls_to_scrape, scraped):
        if isinstance(text, str) and len(text) > 100:
            parts.append(f"\n--- Full page: {url} ---\n{text[:3000]}")

    return "\n\n".join(parts) if parts else "No relevant information found."


# ────────────────────────────────────────────────────────────────────────────
# Agent class
# ────────────────────────────────────────────────────────────────────────────

class CompanyIntelligenceAgent:
    """
    Company Intelligence Agent — LangGraph state machine with 3 parallel specialist nodes.

    Graph:
        START → router ─[proceed]→ financial_node ─┐
                                 → market_node     ─→ report_node → END
                                 → product_node    ─┘
               router ─[reject]→ END
    """

    def __init__(
        self,
        llm_connector: OpenAIConnector,
        fast_llm_connector: Optional[OpenAIConnector] = None,
    ) -> None:
        self._llm      = llm_connector
        self._fast_llm = fast_llm_connector or llm_connector
        self._graph    = self._build_graph()

    # ------------------------------------------------------------------ #
    # Graph construction                                                   #
    # ------------------------------------------------------------------ #

    def _build_graph(self) -> Any:
        workflow = StateGraph(AgentState)

        # Register nodes
        workflow.add_node("router",     self._router_node)
        workflow.add_node("dispatcher", self._dispatcher_node)  # pass-through fan-out
        workflow.add_node("financial",  self._financial_node)
        workflow.add_node("market",     self._market_node)
        workflow.add_node("product",    self._product_node)
        workflow.add_node("report",     self._report_node)

        # Entry
        workflow.add_edge(START, "router")

        # Router → conditional: proceed to dispatcher or reject
        workflow.add_conditional_edges(
            "router",
            self._route_after_validation,
            {
                "proceed": "dispatcher",
                "reject":  END,
            },
        )

        # Dispatcher → parallel fan-out using direct edges.
        # LangGraph runs all nodes reachable from the same super-step concurrently.
        workflow.add_edge("dispatcher", "financial")
        workflow.add_edge("dispatcher", "market")
        workflow.add_edge("dispatcher", "product")

        # All three specialist nodes converge at report
        workflow.add_edge("financial", "report")
        workflow.add_edge("market",    "report")
        workflow.add_edge("product",   "report")

        # Report is terminal
        workflow.add_edge("report", END)

        return workflow.compile()

    # ------------------------------------------------------------------ #
    # Routing helper                                                       #
    # ------------------------------------------------------------------ #

    @staticmethod
    def _route_after_validation(state: AgentState) -> Literal["proceed", "reject"]:
        return "proceed" if state.get("is_valid_request", True) else "reject"

    @staticmethod
    async def _dispatcher_node(state: AgentState) -> Dict[str, Any]:
        """
        Pass-through fan-out node.
        Does no computation — simply allows LangGraph to dispatch to all three
        downstream specialist nodes (financial, market, product) in the same super-step,
        which LangGraph executes concurrently.
        """
        return {}

    # ------------------------------------------------------------------ #
    # Node: Router                                                         #
    # ------------------------------------------------------------------ #

    async def _router_node(self, state: AgentState) -> Dict[str, Any]:
        """Validates the request. Fast-path skips LLM; falls back to LLM for edge cases."""
        company = state.get("company_name", "").strip()
        region  = state.get("company_region", "").strip()

        # Fast-path: looks like a real request
        if len(company) > 1 and len(region) > 1:
            return {
                "is_valid_request": True,
                "messages": [
                    SystemMessage(content=SYSTEM_PROMPT),
                    HumanMessage(content=f"Company: {company}\nRegion: {region}"),
                ],
            }

        # LLM fallback
        resp = await self._fast_llm.ainvoke([
            SystemMessage(content=ROUTER_PROMPT),
            HumanMessage(content=f"company_name={company!r}, company_region={region!r}"),
        ])
        try:
            data  = json.loads(resp.content)
            valid = bool(data.get("valid", False))
            reason = data.get("reason", "")
        except Exception:
            valid  = False
            reason = "Could not parse validation response."

        return {
            "is_valid_request": valid,
            "rejection_reason": reason if not valid else None,
            "messages": [AIMessage(content=f"Rejected: {reason}")] if not valid else [
                SystemMessage(content=SYSTEM_PROMPT),
                HumanMessage(content=f"Company: {company}\nRegion: {region}"),
            ],
        }

    # ------------------------------------------------------------------ #
    # Node: Financial Analysis                                             #
    # ------------------------------------------------------------------ #

    async def _financial_node(self, state: AgentState) -> Dict[str, Any]:
        """Searches for financial intelligence and returns a FinancialAnalysis sub-report."""
        company = state.get("company_name", "")
        region  = state.get("company_region", "")

        queries = [
            f"{company} {region} annual revenue 2024",
            f"{company} funding rounds investment valuation",
            f"{company} financial results profitability",
        ]

        context = await _search_and_scrape(queries, max_results=4, max_pages=3)

        messages = [
            SystemMessage(content=FINANCIAL_SYSTEM),
            HumanMessage(content=(
                f"Company: {company}\nRegion: {region}\n\n"
                f"Retrieved context:\n{context}\n\n"
                "Extract structured financial intelligence from the above."
            )),
        ]

        result: FinancialAnalysis = await self._llm.ainvoke_structured(
            messages, response_model=FinancialAnalysis
        )

        return {
            "financial_analysis": result,
            "messages": [AIMessage(content=f"[Financial node] Analysis complete for {company}.")],
        }

    # ------------------------------------------------------------------ #
    # Node: Market Positioning                                             #
    # ------------------------------------------------------------------ #

    async def _market_node(self, state: AgentState) -> Dict[str, Any]:
        """Searches for competitive & market intelligence and returns a MarketPositioning sub-report."""
        company = state.get("company_name", "")
        region  = state.get("company_region", "")

        queries = [
            f"{company} {region} market share competitors",
            f"{company} competitive landscape positioning 2024",
            f"{company} strategic acquisitions partnerships expansion",
        ]

        context = await _search_and_scrape(queries, max_results=4, max_pages=3)

        messages = [
            SystemMessage(content=MARKET_SYSTEM),
            HumanMessage(content=(
                f"Company: {company}\nRegion: {region}\n\n"
                f"Retrieved context:\n{context}\n\n"
                "Extract structured market positioning intelligence from the above."
            )),
        ]

        result: MarketPositioning = await self._llm.ainvoke_structured(
            messages, response_model=MarketPositioning
        )

        return {
            "market_positioning": result,
            "messages": [AIMessage(content=f"[Market node] Analysis complete for {company}.")],
        }

    # ------------------------------------------------------------------ #
    # Node: Product Intelligence                                           #
    # ------------------------------------------------------------------ #

    async def _product_node(self, state: AgentState) -> Dict[str, Any]:
        """Searches for product & technology intelligence and returns a ProductAnalysis sub-report."""
        company = state.get("company_name", "")
        region  = state.get("company_region", "")

        queries = [
            f"{company} products services overview",
            f"{company} technology platform features 2024",
            f"{company} pricing model monetisation",
        ]

        context = await _search_and_scrape(queries, max_results=4, max_pages=3)

        messages = [
            SystemMessage(content=PRODUCT_SYSTEM),
            HumanMessage(content=(
                f"Company: {company}\nRegion: {region}\n\n"
                f"Retrieved context:\n{context}\n\n"
                "Extract structured product intelligence from the above."
            )),
        ]

        result: ProductAnalysis = await self._llm.ainvoke_structured(
            messages, response_model=ProductAnalysis
        )

        return {
            "product_analysis": result,
            "messages": [AIMessage(content=f"[Product node] Analysis complete for {company}.")],
        }

    # ------------------------------------------------------------------ #
    # Node: Report Assembly                                                #
    # ------------------------------------------------------------------ #

    async def _report_node(self, state: AgentState) -> Dict[str, Any]:
        """
        Assembles the three specialist sub-reports into a single StructuredBusinessAnalysis.
        Also runs a quick search for recent news and key executives.
        """
        company  = state.get("company_name", "")
        region   = state.get("company_region", "")
        fin      = state.get("financial_analysis")
        market   = state.get("market_positioning")
        product  = state.get("product_analysis")

        def _fmt(obj) -> str:
            if obj is None:
                return "Not available."
            return obj.model_dump_json(indent=2)

        # Brief supplementary search for news & executives
        news_ctx = await _search_and_scrape(
            [f"{company} {region} CEO executives leadership",
             f"{company} latest news 2024"],
            max_results=3, max_pages=2
        )

        synthesis_prompt = (
            f"Company: {company}\nRegion: {region}\n\n"
            "=== Financial Analysis ===\n"    + _fmt(fin)    + "\n\n"
            "=== Market Positioning ===\n"    + _fmt(market) + "\n\n"
            "=== Product Intelligence ===\n"   + _fmt(product) + "\n\n"
            "=== Supplementary context (executives, news) ===\n" + news_ctx + "\n\n"
            "Produce the final StructuredBusinessAnalysis using all of the above. "
            "Collect all source URLs from the three analyses into the top-level sources field."
        )

        messages = [
            SystemMessage(content=REPORT_SYSTEM),
            HumanMessage(content=synthesis_prompt),
        ]

        report: StructuredBusinessAnalysis = await self._llm.ainvoke_structured(
            messages, response_model=StructuredBusinessAnalysis
        )

        # Embed the typed sub-reports directly (no need to re-parse them)
        report.financial_analysis = fin
        report.market_positioning  = market
        report.product_analysis    = product

        return {"structured_report": report}

    # ------------------------------------------------------------------ #
    # Public API                                                           #
    # ------------------------------------------------------------------ #

    async def generate_report(
        self,
        company_name: str,
        company_region: str,
    ) -> StructuredBusinessAnalysis:
        """
        Runs the full LangGraph pipeline and returns the assembled intelligence report.
        Raises ValueError if the router rejects the request.
        """
        initial_state: AgentState = {
            "company_name":   company_name,
            "company_region": company_region,
            "messages":       [],
            "is_valid_request": True,
        }

        final_state = await self._graph.ainvoke(
            initial_state,
            config={"recursion_limit": 30},
        )

        if not final_state.get("is_valid_request", True):
            raise ValueError(final_state.get("rejection_reason", "Invalid request."))

        report = final_state.get("structured_report")
        if report is None:
            raise RuntimeError("Agent completed without producing a structured report.")

        return report
