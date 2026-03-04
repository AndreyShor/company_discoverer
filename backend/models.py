from pydantic import BaseModel, Field
from typing import List, Optional

class CompanyReportRequest(BaseModel):
    company_name: str
    company_region: str

class Executive(BaseModel):
    name: str = Field(description="Name of the key executive")
    role: str = Field(description="Role or title of the executive")

class StructuredBusinessAnalysis(BaseModel):
    company_name: str = Field(description="The formal name of the company")
    overview: str = Field(description="A brief, comprehensive overview (1-2 paragraphs) of what the company does, its industry, and main products or services.")
    key_executives: List[Executive] = Field(description="List of key executives (e.g., CEO, Founders).")
    financial_summary: Optional[str] = Field(description="Any retrieved financial information, funding rounds, or revenue indicators. If none found, state 'Not explicitly available'.")
    recent_news: List[str] = Field(description="3-5 bullet points of recent news, developments, or milestones based on the retrieved data.")
    competitors: List[str] = Field(description="List of assumed or stated competitors based on the industry context.")
    sources: List[str] = Field(description="List of URLs or source titles where this information was retrieved from.")
