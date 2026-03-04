from __future__ import annotations

from typing import Optional

from pydantic import BaseModel, Field


class CompanyReportRequest(BaseModel):
    company_name: str = Field(min_length=1, max_length=256)
    country: str = Field(min_length=2, max_length=64)


class CompanyReportResponse(BaseModel):
    company_name: str
    country: str
    summary: str
    sources: list[str] = Field(default_factory=list)
    metadata: dict = Field(default_factory=dict)


class CompanySearchResult(BaseModel):
    company_name: str
    country: str
    score: float
    snippet: Optional[str] = None
