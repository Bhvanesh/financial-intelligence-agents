import os
import re
from dotenv import load_dotenv
from schemas import RiskOutput
from langchain_openai import ChatOpenAI
from state import AnalyzerState
import time
import logging
load_dotenv()
logger = logging.getLogger(__name__)

_llm = ChatOpenAI(model = os.getenv("OPENAI_MODEL"), temperature=0)
_risk_llm = _llm.with_structured_output(RiskOutput)

def _normalize(text: str) -> str:
    text = (text.replace("\u2019", "'").replace("\u2018", "'").replace("\u201c", "'").replace("\u201d", '"'))
    text = re.sub(r"\$\s+", "$", text)
    text = re.sub(r"\s+", " ", text).strip().lower()
    return text.rstrip(".;,")


def risk_detector_node(state: AnalyzerState) -> dict:
    starttime = time.time()
    logger.info("Risk detector node started at %s", starttime)
    text = state["report_text"]
    prompt = f"""You are a risk analyst reviewing an earnings report.
Identify risks that the text itself supports.

Rules:
- Use ONLY the text below. Do not use outside knowledge about the company.
- Each risk must include an evidence field: an exact, verbatim quote copied from the text.
- Evidence must be one or two consecutive sentences copied verbatim.
- Do NOT use table rows as evidence. Only use full sentences from the narrative text.
- Strictly Do NOT quote table rows as evidence. IF A table row looks like:
  "Label $1,234 $5,678 (8) 23" — numbers with no connecting words, THEN you MUST find the narrative paragraph that describes the same data.
- If the text supports no risks, return an empty list.
- The description may only state facts (numbers, causes, entities) that appear in the evidence.
- SKIP any risk from the Cautionary Note Regarding Forward-Looking Statements section and legal disclaimers.
- Prioritize quarter-over-quarter declines, capital and liquidity ratio changes, and credit provisions.

Text:
{text}"""

    result = _risk_llm.invoke(prompt)

    haystack = _normalize(text)
    risks = []
    for item in result.risks:
        entry = item.model_dump()
        entry["evidence_verified"] = _normalize(item.evidence) in haystack
        if entry["evidence_verified"]:
         risks.append(entry)
    endtime = time.time()
    logger.info("Risk detector node ended at %s", endtime)
    logger.info("Risk detector node duration: %s seconds", endtime - starttime)
    return {"risks": risks}
