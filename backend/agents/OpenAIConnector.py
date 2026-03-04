from __future__ import annotations
from typing import Any, Dict, List, Optional, Type
import os
import asyncio
from langchain_openai import ChatOpenAI
from langchain_core.messages import AIMessage
from langchain_core.runnables import Runnable
from pydantic import BaseModel


class OpenAIConnector:
    """
    Simplified OpenAI LLM connector for Company Discoverer.
    Wraps ChatOpenAI with tool-binding and structured output support.
    Mirrors the pattern from LegalAssistant's OpenAIConnector.
    """

    def __init__(
        self,
        model: str = "gpt-4o-mini",
        temperature: float = 0.0,
        max_tokens: Optional[int] = 4000,
    ) -> None:
        api_key = os.getenv("OPENAI_KEY") or os.getenv("OPENAI_API_KEY")
        if not api_key:
            raise ValueError("OPENAI_KEY is not set in environment variables.")

        self.model = model

        self._langchain_llm = ChatOpenAI(
            model=self.model,
            openai_api_key=api_key,
            temperature=temperature,
            max_tokens=max_tokens,
        )

    # ------------------------------------------------------------------ #
    #  Sync / Async invocation                                             #
    # ------------------------------------------------------------------ #

    def invoke(self, input_data: Any, **kwargs) -> AIMessage:
        """Delegate sync invocation to LangChain ChatOpenAI."""
        tools = kwargs.pop("tools", None)
        tool_choice = kwargs.pop("tool_choice", None)
        if tools:
            runnable = self._langchain_llm.bind_tools(tools, tool_choice=tool_choice)
            return runnable.invoke(input_data, **kwargs)
        return self._langchain_llm.invoke(input_data, **kwargs)

    async def ainvoke(self, input_data: Any, **kwargs) -> AIMessage:
        """Delegate async invocation to LangChain ChatOpenAI."""
        tools = kwargs.pop("tools", None)
        tool_choice = kwargs.pop("tool_choice", None)
        if tools:
            runnable = self._langchain_llm.bind_tools(tools, tool_choice=tool_choice)
            return await runnable.ainvoke(input_data, **kwargs)
        return await self._langchain_llm.ainvoke(input_data, **kwargs)

    # ------------------------------------------------------------------ #
    #  Structured output                                                   #
    # ------------------------------------------------------------------ #

    def with_structured_output(self, schema: Type[BaseModel], **kwargs) -> Runnable:
        """Return a runnable that produces structured output conforming to schema."""
        return self._langchain_llm.with_structured_output(schema, **kwargs)

    async def ainvoke_structured(self, input_data: Any, response_model: Type[BaseModel], **kwargs) -> BaseModel:
        """Async structured output call."""
        runnable = self._langchain_llm.with_structured_output(response_model)
        return await runnable.ainvoke(input_data)

    # ------------------------------------------------------------------ #
    #  Tool binding passthrough                                            #
    # ------------------------------------------------------------------ #

    def bind_tools(self, *args, **kwargs) -> Runnable:
        """Delegate tool binding to LangChain ChatOpenAI."""
        return self._langchain_llm.bind_tools(*args, **kwargs)
