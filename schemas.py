from pydantic import BaseModel, Field
from typing import Literal
from datetime import datetime

class FinancialMetrics(BaseModel):
    
    company_name: str | None = Field(description="Name of the company, or null if not stated")
    fiscal_period: str | None = Field(description="Current reporting period as 'Q<quarter> <year>', for example 'Q3 2026'. Null if not stated")
    revenue_usd_millions: float | None = Field(description="Total revenue for the current quarter in USD millions, or null if not stated")
    revenue_prior_quarter_usd_millions: float | None = Field(description="Total revenue for the immediately preceding quarter in USD millions, or null if not stated")
    revenue_prior_year_usd_millions: float | None = Field(description="Total revenue for the same quarter one year earlier in USD millions, or null if not stated")
    operating_income_usd_millions: float | None = Field(description="Operating income for the current quarter in USD millions, or null if not stated")
    net_income_usd_millions: float | None = Field(description="Net income for the current quarter in USD millions, or null if not stated")
    net_income_prior_quarter_usd_millions: float | None = Field(description="Net income for the immediately preceding quarter in USD millions, or null if not stated")
    net_income_prior_year_usd_millions: float | None = Field(description="Net income for the same quarter one year earlier in USD millions, or null if not stated")
    diluted_eps_usd: float | None = Field(description="Diluted EPS for the current quarter in USD, or null if not stated")
    diluted_eps_prior_quarter_usd: float | None = Field(description="Diluted EPS for the immediately preceding quarter in USD, or null if not stated")
    diluted_eps_prior_year_usd: float | None = Field(description="Diluted EPS for the same quarter one year earlier in USD, or null if not stated")
    gross_margin_percent: float | None = Field(description="Gross margin for the current quarter as a percentage, or null if not stated")


class AnalystOutput(BaseModel):
    summary: str = Field(description="Two to three sentence summary of the quarter based only on the provided metrics")
    key_facts: list[str] = Field(description="Factual statements, each naming one provided metric and its value. No opinions or evaluative language.")
    
class RiskItem(BaseModel):
    category: Literal["credit", "market","liquidity", "regulatory_legal", "operational", "macro", "other"] = Field(description="Category of the risk")
    description: str = Field(description="One sentance Description of the risk")
    evidence: str = Field(description="An exact, verbatim sentence or phrase copied from the report text that supports this risk")

class RiskOutput(BaseModel):
    risks: list[RiskItem] = Field(description="Risks explicitly supported by the text. Empty list if none.")

class ReporterOutput(BaseModel):
    verdict: Literal["bullish", "neutral", "bearish"] = Field(description="Overall verdict: bullish if performance is strong, bearish if weak, neutral if mixed")
    executive_summary: str = Field(description="Three to four sentance executive summary synthesizing financial performance. trends, and key risks")
    highlights: list[str] = Field(description="List of key takeaways from the report, each as a concise factual statement")
    risk_summary: str = Field(description="One sentance summarizing the key risks identified in the report")

# Route definitions:
# full_analysis        → extractor + risk_detector + analyst + reporter
# metrics_only         → extractor only
# risks_only           → risk_detector only
# metrics_and_analysis → extractor + analyst
# summary_only         → extractor + analyst + reporter (no risks)

class SupervisorOutput(BaseModel):
    route: Literal[ "full_analysis",
        "metrics_only",
        "risks_only",
        "metrics_and_analysis",
        "summary_only"] = Field(description = "Which agent to trigger based on user's input")
    reason: str = Field(description = "One sentence explanation of why this route is selected")



class AnalyzeRequest(BaseModel):
    user_prompt: str = Field(
        description="What you want to know about the document",
        example="Give me the complete analysis"
        )


class AnalysisResponse(BaseModel):
    id:            int
    filename:      str
    user_prompt:   str
    route:         str 
    company_name:  str | None
    fiscal_period: str | None
    metrics:       dict | None
    analysis:      dict | None
    risks:         list | None
    report:        dict | None
    created_at:    datetime

    model_config = {"from_attributes": True}

class AnalysisSummaryResponse(BaseModel):
    id : int
    filename: str
    user_prompt: str
    route: str
    company_name: str | None
    fiscal_period: str | None
    created_at: datetime

    model_config = {"from_attributes": True}


class MetricsOnlyResponse(BaseModel):
    id:           int
    filename:     str
    user_prompt:  str
    route:        str
    company_name: str | None
    fiscal_period: str | None
    metrics:      dict
    created_at:   datetime
    model_config = {"from_attributes": True}


class RisksOnlyResponse(BaseModel):
    id:          int
    filename:    str
    user_prompt: str
    route:       str
    risks:       list
    created_at:  datetime
    model_config = {"from_attributes": True}


class TrendsResponse(BaseModel):
    id:           int
    filename:     str
    user_prompt:  str
    route:        str
    company_name: str | None
    fiscal_period: str | None
    metrics:      dict
    analysis:     dict
    created_at:   datetime
    model_config = {"from_attributes": True}


class SummaryResponse(BaseModel):
    id:           int
    filename:     str
    user_prompt:  str
    route:        str
    company_name: str | None
    fiscal_period: str | None
    metrics:      dict
    analysis:     dict
    report:       dict
    created_at:   datetime
    model_config = {"from_attributes": True}


class FullAnalysisResponse(BaseModel):
    id:           int
    filename:     str
    user_prompt:  str
    route:        str
    company_name: str | None
    fiscal_period: str | None
    metrics:      dict
    analysis:     dict
    risks:        list
    report:       dict
    created_at:   datetime
    model_config = {"from_attributes": True}


#-----API Key schemas-----

class APIKeyRegisterRequest(BaseModel):
    owner_name: str = Field(min_length=2, max_length=100, description = "Your name or organization name")

class APIKeyResponse(BaseModel):
    id: int
    key: str
    owner_name: str
    is_active: bool
    created_at: datetime
    message:    str = "Store this key safely. It will be shown only once."

    model_config = {"from_attributes": True}