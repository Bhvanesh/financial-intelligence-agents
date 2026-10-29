import os
from dotenv import load_dotenv
from langchain_openai import ChatOpenAI
from schemas import FinancialMetrics
from state import AnalyzerState
import time
import logging
logger = logging.getLogger(__name__)
load_dotenv()

_llm = ChatOpenAI(model = os.getenv("OPENAI_MODEL"), temperature=0)
_extractor_llm = _llm.with_structured_output(FinancialMetrics)

def extractor_node(state: AnalyzerState) -> dict:
    starttime = time.time()
    logger.info("Extractor node started at %s", starttime)
    text = state["report_text"]
    prompt = f"""You are a financial data extraction assistant.
Extract the requested fields from the text below.

Rules:
- Use ONLY information stated in the text.
- If a value is not stated, return null. Never guess or estimate.
- Convert all dollar amounts to USD millions.

Text:
{text}"""
    result = _extractor_llm.invoke(prompt)
    endtime = time.time()
    logger.info("Extractor node ended at %s", endtime)
    logger.info("Extractor node duration: %s seconds", endtime - starttime)
    return {"metrics": result.model_dump()}