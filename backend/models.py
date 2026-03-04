from pydantic import BaseModel, Field
from typing import List, Optional


# ─── API request ────────────────────────────────────────────────────────────

class CompanyReportRequest(BaseModel):
    company_name: str
    company_region: str


# ─── Shared building block ───────────────────────────────────────────────────

class Executive(BaseModel):
    name: str = Field(description="Name of the key executive")
    role: str = Field(description="Role or title of the executive")


# ─── Intermediate structured outputs (one per specialist node) ───────────────

class FinancialAnalysis(BaseModel):
    """Structured output produced by the Financial Analysis agent node."""
    revenue: Optional[str] = Field(
        default=None,
        description="Most recent annual or quarterly revenue figures, or 'Not publicly available'."
    )
    funding_rounds: List[str] = Field(
        default_factory=list,
        description="List of known funding rounds (amount, date, lead investors)."
    )
    valuation: Optional[str] = Field(
        default=None,
        description="Last known company valuation or market capitalisation."
    )
    profitability: Optional[str] = Field(
        default=None,
        description="Profitability status: profitable, pre-profit, or details if known."
    )
    years_to_profitability: Optional[str] = Field(
        default=None,
        description="How many years it took the company to become profitable after founding. E.g. '12 years (founded 2010, profitable 2022)'. State 'Not yet profitable' or 'Not publicly available' if unknown."
    )
    key_financial_metrics: List[str] = Field(
        default_factory=list,
        description="Any other notable financial KPIs: MAU, GMV, burn rate, etc."
    )
    sources: List[str] = Field(
        default_factory=list,
        description="URLs or titles of sources used."
    )


class MarketPositioning(BaseModel):
    """Structured output produced by the Market Positioning agent node."""
    market_segment: str = Field(
        description="The primary industry / market segment the company competes in."
    )
    geographic_presence: List[str] = Field(
        default_factory=list,
        description="Countries or regions where the company actively operates."
    )
    target_customers: str = Field(
        description="Primary customer segments (e.g., B2B enterprise, B2C consumers, SMBs)."
    )
    competitive_advantages: List[str] = Field(
        default_factory=list,
        description="Key differentiators or moats vs. competitors."
    )
    competitors: List[str] = Field(
        default_factory=list,
        description="Named direct competitors."
    )
    recent_strategic_moves: List[str] = Field(
        default_factory=list,
        description="Recent acquisitions, partnerships, expansions, or pivots."
    )
    sources: List[str] = Field(
        default_factory=list,
        description="URLs or titles of sources used."
    )


class ProductAnalysis(BaseModel):
    """Structured output produced by the Product agent node."""
    core_products: List[str] = Field(
        description="List of the company's main products or services."
    )
    technology_stack: List[str] = Field(
        default_factory=list,
        description="Known technologies, platforms, or infrastructure powering their products."
    )
    product_highlights: List[str] = Field(
        default_factory=list,
        description="Notable features, recent launches, or differentiating capabilities."
    )
    pricing_model: Optional[str] = Field(
        default=None,
        description="Pricing or monetisation strategy (subscription, freemium, usage-based, etc.)."
    )
    sources: List[str] = Field(
        default_factory=list,
        description="URLs or titles of sources used."
    )


# ─── Final report (assembled by _report_node from the three above) ───────────

class StructuredBusinessAnalysis(BaseModel):
    """Complete intelligence report returned to the API consumer."""
    company_name: str = Field(description="The formal name of the company.")
    year_founded: Optional[str] = Field(
        default=None,
        description="The year the company was founded (e.g. '2010'). State 'Not publicly available' if unknown."
    )
    overview: str = Field(
        description="A concise 2-3 paragraph executive summary of the company."
    )
    key_executives: List[Executive] = Field(
        description="List of key executives (CEO, founders, C-suite)."
    )
    financial_analysis: Optional[FinancialAnalysis] = Field(
        default=None,
        description="Structured financial intelligence gathered by the Financial Analysis node."
    )
    market_positioning: Optional[MarketPositioning] = Field(
        default=None,
        description="Structured market & competitive intelligence from the Market Positioning node."
    )
    product_analysis: Optional[ProductAnalysis] = Field(
        default=None,
        description="Structured product intelligence from the Product node."
    )
    recent_news: List[str] = Field(
        default_factory=list,
        description="3-5 recent news items or milestones."
    )
    sources: List[str] = Field(
        default_factory=list,
        description="Deduplicated list of all source URLs referenced in the report."
    )
