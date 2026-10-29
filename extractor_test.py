import os
from dotenv import load_dotenv
from langchain_openai import ChatOpenAI
from schemas import FinancialMetrics

load_dotenv()

llm = ChatOpenAI(
    model=os.getenv("OPENAI_MODEL"), temperature=0
)
extractor_llm = llm.with_structured_output(FinancialMetrics)

SAMPLE_FULL = """
Acme Corp Reports Third Quarter Fiscal 2026 Results.
Net sales were $94.9 billion, up 6 percent year over year.
Operating income was $29.6 billion and net income was $21.4 billion.
Diluted earnings per share was $1.40. Gross margin was 46.2 percent.
"""

SAMPLE_EMPTY = """
Acme Corp had a strong quarter and management expects continued growth.
"""

def extract(text:str) -> FinancialMetrics:
        prompt = f"""You are a financial data extraction assistant.
Extract the requested fields from the text below.

Rules:
- Use ONLY information stated in the text.
- If a value is not stated, return null. Never guess or estimate.
- Convert all dollar amounts to USD millions.

Text:
{text}"""
        return extractor_llm.invoke(prompt)

for name, text in [("FULL", SAMPLE_FULL), ("EMPTY", SAMPLE_EMPTY)]:
    result = extract(text)
    print(f"---{name}---")
    print(type(result))
    print(result.model_dump_json(indent=2))