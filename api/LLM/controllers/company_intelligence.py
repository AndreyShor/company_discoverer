from __future__ import annotations

from langchain_openai import ChatOpenAI
from langchain.prompts import ChatPromptTemplate

from core.config import settings
from core.logging import get_logger
from models.company_models import CompanyReportResponse

logger = get_logger(__name__)

_SYSTEM_PROMPT = (
    "You are a corporate intelligence analyst. "
    "Given a company name and country, produce a concise structured business intelligence summary. "
    "Include: overview, key products/services, recent news, and notable risk factors. "
    "Keep the response factual, neutral, and under 400 words."
)

_HUMAN_TEMPLATE = "Company: {company_name}\nCountry: {country}"


async def run_company_intelligence(company_name: str, country: str) -> CompanyReportResponse:
    """Invoke the LangChain LLM pipeline to generate a company intelligence report."""
    llm = ChatOpenAI(
        model="gpt-4o-mini",
        temperature=0.2,
        api_key=settings.openai_api_key,
    )

    prompt = ChatPromptTemplate.from_messages(
        [
            ("system", _SYSTEM_PROMPT),
            ("human", _HUMAN_TEMPLATE),
        ]
    )

    chain = prompt | llm
    logger.info("llm_pipeline_start", company=company_name, country=country)
    response = await chain.ainvoke({"company_name": company_name, "country": country})
    summary: str = response.content if hasattr(response, "content") else str(response)

    return CompanyReportResponse(
        company_name=company_name,
        country=country,
        summary=summary,
        sources=[],
    )
