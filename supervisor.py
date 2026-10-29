from dotenv import load_dotenv
import os
from langchain_openai import ChatOpenAI
from schemas import SupervisorOutput
from state import AnalyzerState
import logging
import time

logger = logging.getLogger(__name__)  

load_dotenv()

_llm = ChatOpenAI(model=os.getenv("OPENAI_MODEL"), temperature = 0)
_supervisor_llm = _llm.with_structured_output(SupervisorOutput)

def supervisor_node(state: AnalyzerState) -> dict:
    starttime = time.time()
    logger.info("Supervisor node started at %s", starttime)
    user_prompt = state["user_prompt"]
    prompt = f"""You are a supervisor that routes user requests
to the correct financial analysis agents.

Available routes:
- full_analysis:         User wants complete analysis — metrics,
                         trends, risks, and executive summary
- metrics_only:          User wants only financial figures —
                         revenue, income, EPS, margins
- risks_only:            User wants only risk factors and
                         risk assessment
- metrics_and_analysis:  User wants financial figures plus
                         trend analysis and percentage changes
- summary_only:          User wants executive summary and verdict
                         without detailed risk breakdown

Rules:
- If the request is vague or unclear → default to full_analysis
- If the request mentions "risk" or "risks" → risks_only
  UNLESS they also ask for metrics or summary
- If the request mentions only "metrics", "figures", "numbers",
  "financials", or "extract" → metrics_only
- If the request mentions "analysis", "trends", "compare",
  "QoQ", "YoY" → metrics_and_analysis
- If the request mentions "summary", "verdict", "overview",
  "executive" → summary_only
- If the request mentions multiple things → full_analysis

User request: {user_prompt}"""
    result = _supervisor_llm.invoke(prompt)
    endtime = time.time()
    logger.info("Supervisor node ended at %s", endtime)
    logger.info("Supervisor node duration: %s seconds", endtime - starttime)
    return {"route": result.route}
