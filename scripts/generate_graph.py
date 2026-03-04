"""Generate a visual graph of the LangGraph company intelligence state machine."""
from __future__ import annotations

import sys

from langgraph.graph import StateGraph, END
from typing import TypedDict


class IntelligenceState(TypedDict):
    company_name: str
    country: str
    raw_data: str
    summary: str
    done: bool


def build_graph() -> StateGraph:
    graph = StateGraph(IntelligenceState)

    graph.add_node("fetch_data", lambda s: {**s, "raw_data": f"<fetched data for {s['company_name']}>"})
    graph.add_node("summarise", lambda s: {**s, "summary": f"Summary of {s['raw_data']}", "done": True})

    graph.set_entry_point("fetch_data")
    graph.add_edge("fetch_data", "summarise")
    graph.add_edge("summarise", END)

    return graph


def main() -> None:
    graph = build_graph()
    compiled = graph.compile()
    try:
        image_bytes = compiled.get_graph().draw_mermaid_png()
        output_path = "company_intelligence_graph.png"
        with open(output_path, "wb") as f:
            f.write(image_bytes)
        print(f"Graph saved to {output_path}")
    except Exception as exc:
        print(f"Could not render graph image (install graphviz): {exc}", file=sys.stderr)
        print(compiled.get_graph().draw_mermaid())


if __name__ == "__main__":
    main()
