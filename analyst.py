import os
import json
import re
from dotenv import load_dotenv
from langchain_openai import ChatOpenAI
from opentelemetry import metrics
from schemas import AnalystOutput
from state import AnalyzerState
from langchain_core.tools import tool
from langchain_core.messages import HumanMessage, ToolMessage
from langchain_core.prompts import ChatPromptTemplate
import time
import logging


logger = logging.getLogger(__name__)
load_dotenv()

_llm = ChatOpenAI(model=os.getenv("OPENAI_MODEL"), temperature=0)

@tool
def calculate_change(current: float | None, prior: float | None) -> str:
       """
    Calculate percentage change from prior period to current period.
    Use this to compute QoQ or YoY changes for any metric.
    Returns a string with the percentage, or 'unavailable' if data missing.
    
    Args:
        current: The current period value
        prior: The prior period value to compare against
    """
       if current is None or prior is None or prior == 0:
           return "unavailable - one or both values missing"
       result = round((current - prior) / abs(prior) * 100, 2)
       direction = "increase" if result > 0 else "decline"
       return f"{result}% {direction}"

@tool  
def calculate_margin(income: float | None, revenue: float | None) -> str:
    """
    Calculate net margin as a percentage of revenue.
    Use this to compute profitability margins.
    
    Args:
        income: Net income in USD millions
        revenue: Total revenue in USD millions  
    """
    if income is None or revenue is None or revenue == 0:
        return "unavailable — one or both values missing"
    result = round(income / revenue * 100, 2)
    return f"{result}%"


_tools = [calculate_change, calculate_margin]
_tools_by_name = {t.name: t for t in _tools}
_llm_with_tools = _llm.bind_tools(_tools)
_analyst_llm = _llm.with_structured_output(AnalystOutput)


def _net_margin_percent(metrics: dict) -> float | None:
    revenue = metrics.get("revenue_usd_millions")
    net_income = metrics.get("net_income_usd_millions")
    if revenue is None or net_income is None or revenue == 0:
        return None
    return round(net_income/revenue * 100, 2)



def analyst_node(state: AnalyzerState) -> dict:
    starttime = time.time()
    logger.info("Analyst node started at %s", starttime)
    metrics = state["metrics"]
    #net_margin = _net_margin_percent(metrics)
    prompt = f"""You are a financial analyst.Use the calculate_change and calculate_margin tools to compute all relevant metrics, then write a financial analysis.
Rules:
- Use calculate_change for ALL QoQ and YoY percentage changes.
- Use calculate_margin for net margin.
- Never calculate anything yourself — always use the tools.
- Only skip a calculation if both values are null.

Financial metrics:
{json.dumps(metrics, indent=2)}

Calculate: revenue QoQ%, revenue YoY%, net income QoQ%,
net income YoY%, EPS QoQ%, EPS YoY%, and net margin."""
    messages = [HumanMessage(content=prompt)]

    while True:
        response = _llm_with_tools.invoke(messages)
        messages.append(response)

        if not response.tool_calls:
            break

        for tool_call in response.tool_calls:
            tool_fn = _tools_by_name[tool_call["name"]]
            result = tool_fn.invoke(tool_call["args"])
            messages.append(ToolMessage(content=str(result), tool_call_id = tool_call["id"]))

        analysis_prompt = f"""Based on your calculations, write a structured analysis.
        Rules:
        - Use ONLY the values your tools returned.
        - Do not recalculate anything.
        - Every key_fact must cite a specific metric and calculated value.

        Original metrics: {json.dumps(metrics, indent=2)}"""   

        result = _analyst_llm.invoke(messages + [HumanMessage(content=analysis_prompt)])

        analysis = result.model_dump()
    
        revenue        = metrics.get("revenue_usd_millions")
        revenue_qoq    = metrics.get("revenue_prior_quarter_usd_millions")
        revenue_yoy    = metrics.get("revenue_prior_year_usd_millions")
        net_income     = metrics.get("net_income_usd_millions")
        net_income_qoq = metrics.get("net_income_prior_quarter_usd_millions")
        net_income_yoy = metrics.get("net_income_prior_year_usd_millions")
        eps            = metrics.get("diluted_eps_usd")
        eps_qoq        = metrics.get("diluted_eps_prior_quarter_usd")
        eps_yoy        = metrics.get("diluted_eps_prior_year_usd")
        
        def pct(current, prior):
            if current is None or prior is None or prior == 0:
                return None
            return round((current - prior) / abs(prior) * 100, 2)
        computed = {
            "revenue_qoq_pct":    pct(revenue, revenue_qoq),
            "revenue_yoy_pct":    pct(revenue, revenue_yoy),
            "net_income_qoq_pct": pct(net_income, net_income_qoq),
            "net_income_yoy_pct": pct(net_income, net_income_yoy),
            "eps_qoq_pct":        pct(eps, eps_qoq),
            "eps_yoy_pct":        pct(eps, eps_yoy),
            "net_margin_pct":     round(net_income / revenue * 100, 2) if revenue and net_income else None,}
        
        analysis["computed"] = computed
        analysis["net_margin_percent"] = computed["net_margin_pct"]
        endtime = time.time()
        logger.info("Analyst node ended at %s", endtime)
        logger.info("Analyst node duration: %s seconds", endtime - starttime)
        return {"analysis": analysis}

    


