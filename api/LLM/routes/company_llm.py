from __future__ import annotations

from fastapi import APIRouter, HTTPException, status

from api.LLM.controllers.company_intelligence import run_company_intelligence
from core.logging import get_logger
from models.company_models import CompanyReportRequest, CompanyReportResponse

logger = get_logger(__name__)

router = APIRouter(prefix="/llm", tags=["llm"])


@router.post("/analyze", response_model=CompanyReportResponse)
async def analyze_company(body: CompanyReportRequest) -> CompanyReportResponse:
    """Synchronously run the LLM company intelligence pipeline and return a report."""
    try:
        report = await run_company_intelligence(
            company_name=body.company_name,
            country=body.country,
        )
    except Exception as exc:
        logger.error("llm_analyze_failed", error=str(exc), company=body.company_name)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Intelligence pipeline failed",
        ) from exc

    return report
