import json
from langgraph.graph import StateGraph, START, END
from risk_detector import risk_detector_node
from state import AnalyzerState
from extractor import extractor_node
from analyst import analyst_node
from reporter import Reporter_node as reporter_node
from supervisor import supervisor_node

def route_after_supervisor(state: AnalyzerState) -> str:
    """
    Reads the route from state and returns the next node name.
    LangGraph uses this to decide which edge to follow.
    """
    return state["route"]

def parallel_trigger_node(state: AnalyzerState) -> dict:
    """
    Dummy node for full_analysis route only.
    Does nothing — exists purely so LangGraph
    can fan-out to extractor and risk_detector simultaneously.
    """
    return {}

builder = StateGraph(AnalyzerState)
builder.add_node("supervisor", supervisor_node)
builder.add_node("parallel_trigger",  parallel_trigger_node)
builder.add_node("extractor", extractor_node)
builder.add_node("analyst", analyst_node)
builder.add_node("risk_detector", risk_detector_node)
builder.add_node("reporter", reporter_node)


builder.add_edge(START, "supervisor")

builder.add_conditional_edges("supervisor", route_after_supervisor,{
        "full_analysis":         "parallel_trigger",
        "metrics_only":          "extractor",
        "risks_only":            "risk_detector",
        "metrics_and_analysis":  "extractor",
        "summary_only":          "extractor",
    })

builder.add_edge("parallel_trigger", "extractor")
builder.add_edge("parallel_trigger", "risk_detector")

builder.add_conditional_edges("extractor", lambda state: state["route"], {
        "full_analysis":        "analyst",
        "metrics_only":         END,
        "metrics_and_analysis": "analyst",
        "summary_only":         "analyst",
    })

builder.add_conditional_edges(
    "analyst",
    lambda state: state["route"],
    {
        "full_analysis":        "reporter",
        "metrics_and_analysis": END,
        "summary_only":         "reporter",
    }
)

builder.add_conditional_edges(
    "risk_detector",
    lambda state: state["route"],
    {
        "full_analysis": "reporter",
        "risks_only":    END,
    }
)
builder.add_edge("reporter", END)

'''
builder.add_edge(START, "extractor")
builder.add_edge(START, "risk_detector")
builder.add_edge("extractor", "analyst")
builder.add_edge("analyst", "reporter")
builder.add_edge("risk_detector","reporter")
'''
graph = builder.compile()


if __name__ == "__main__":
    SAMPLE = """
Acme Corp Reports Third Quarter Fiscal 2026 Results.
Net sales were $94.9 billion, up 6 percent year over year.
Operating income was $29.6 billion and net income was $21.4 billion.
Diluted earnings per share was $1.40. Gross margin was 46.2 percent.
"""
    # Test full analysis
    result = graph.invoke({
        "report_text": SAMPLE,
        "user_prompt": "Give me the complete analysis",
        "route":       None,
        "metrics":     None,
        "analysis":    None,
        "risks":       None,
        "report":      None,
    })
    print(json.dumps(result["metrics"],  indent=2))
    print(json.dumps(result["analysis"], indent=2))
    print(json.dumps(result["risks"],    indent=2))
    print(json.dumps(result["report"],   indent=2))
    print(graph.get_graph().draw_mermaid())
    #print(graph.get_graph().draw_ascii())