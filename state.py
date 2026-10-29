from typing import TypedDict

class AnalyzerState(TypedDict):
    report_text: str
    user_prompt: str
    route: str|None
    metrics: dict | None
    analysis: dict |None
    risks: list[dict] | None
    report: dict | None

