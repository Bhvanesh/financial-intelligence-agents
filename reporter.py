import os
import json
from dotenv import load_dotenv
from langchain_openai import ChatOpenAI
from schemas import ReporterOutput
from state import AnalyzerState
import time
import logging
logger = logging.getLogger(__name__)
load_dotenv()

_llm = ChatOpenAI(model=os.getenv("OPENAI_MODEL"), temperature=0)
_reporter_llm = _llm.with_structured_output(ReporterOutput)

def Reporter_node(state: AnalyzerState) -> dict:
    starttime = time.time()
    logger.info("Reporter node started at %s", starttime)
    metrics = state["metrics"]
    analysis = state["analysis"]
    risks = state["risks"]
    
    if analysis is None or metrics is None:
        return {}

    computed = analysis.get("computed", {})

    if risks:
        risk_lines = "\n".join(
            f"- [{r['category'].upper()}] {r['description']} "
            f"(Evidence: {r['evidence']})"
            for r in risks)
    else:
        risk_lines = "No material risks identified."

    prompt = f"""You are a senior financial analyst writing an executive report.Synthesize the information below into a final report.

        Rules:
        - Verdict must follow this logic exactly:
        - bullish: revenue YoY positive AND net income YoY positive
                 AND both QoQ declines are less than 10%
        - bearish: revenue YoY negative OR net income YoY negative
        - neutral: YoY metrics positive but ANY QoQ decline exceeds 10%
  
        FINANCIAL METRICS: {json.dumps(metrics, indent=2)}

        PRE-COMPUTED CHANGES (use these exact numbers, do not recalculate):
        revenue_qoq_pct:    {computed.get('revenue_qoq_pct')}%
        revenue_yoy_pct:    {computed.get('revenue_yoy_pct')}%
        net_income_qoq_pct: {computed.get('net_income_qoq_pct')}%
        net_income_yoy_pct: {computed.get('net_income_yoy_pct')}%
        eps_qoq_pct:        {computed.get('eps_qoq_pct')}%
        eps_yoy_pct:        {computed.get('eps_yoy_pct')}%
        net_margin_pct:     {computed.get('net_margin_pct')}%


        ANALYSIS:
        Summary: {analysis['summary']}
        Net margin: {analysis['net_margin_percent']}%

        RISKS: {risk_lines}"""

    result = _reporter_llm.invoke(prompt)
    endtime = time.time()
    logger.info("Reporter node ended at %s", endtime)
    logger.info("Reporter node duration: %s seconds", endtime - starttime)
    return {"report" : result.model_dump()}
