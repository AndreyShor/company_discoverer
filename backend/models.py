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
    is_large_company: bool = Field(
        description="Whether the company is deemed 'large enough' for a deep financial investigation (e.g. public company, unicorn, or high revenue/headcount)."
    )
    sources: List[str] = Field(
        default_factory=list,
        description="URLs or titles of sources used."
    )


class Investor(BaseModel):
    """Profile of a single investor."""
    name: str = Field(description="Name of the investor (firm or individual).")
    type: Optional[str] = Field(default=None, description="Type: VC, PE, Angel, Corporate, etc.")
    notable_portfolio: List[str] = Field(default_factory=list, description="Other notable companies this investor has backed.")
    reason_for_investing: Optional[str] = Field(default=None, description="Stated or inferred rationale for investing in this company.")


class RevenueYear(BaseModel):
    """Revenue for a single year."""
    year: str = Field(description="Fiscal year, e.g. '2023'.")
    revenue: str = Field(description="Revenue figure and currency, e.g. '$5.1B'.")
    growth: Optional[str] = Field(default=None, description="YoY growth percentage if available.")


class FinancialDeepAnalysis(BaseModel):
    """Deep financial intelligence produced by the Financial Deep-Dive agent node."""
    revenue_over_time: List[RevenueYear] = Field(
        default_factory=list,
        description="Year-by-year revenue progression to show growth trajectory."
    )
    key_investors: List[Investor] = Field(
        default_factory=list,
        description="Profiles of the most significant investors with their rationale."
    )
    investment_thesis: Optional[str] = Field(
        default=None,
        description="Synthesis of the main reasons investors have backed this company — market opportunity, team, moat, timing, etc."
    )
    capital_deployment: List[str] = Field(
        default_factory=list,
        description="How raised capital has been spent: R&D, hiring, acquisitions, marketing, infrastructure, etc."
    )
    expense_strategy: Optional[str] = Field(
        default=None,
        description="Overall expense philosophy — cost discipline, heavy R&D investment, growth-at-all-costs, etc."
    )
    future_outlook: Optional[str] = Field(
        default=None,
        description="Analyst or management projections, growth opportunities, risks, and strategic bets for the next 2-5 years."
    )
    key_risks: List[str] = Field(
        default_factory=list,
        description="Main financial or strategic risks identified from public reporting."
    )
    sources: List[str] = Field(
        default_factory=list,
        description="URLs or titles of sources used in the deep-dive."
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
    financial_deep_analysis: Optional[FinancialDeepAnalysis] = Field(
        default=None,
        description="Deep financial intelligence: revenue trends, investor profiles, capital deployment, and future outlook."
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
