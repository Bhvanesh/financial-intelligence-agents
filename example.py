from typing import TypedDict
from langgraph.graph import StateGraph, START, END

# 1. State: the shared clipboard
class State(TypedDict):
    question: str
    answer: str

# 2. Nodes: functions that return state updates
def classify(state: State):
    return {}  # (could set a category here)

def answer_node(state: State):
    return {"answer": f"You asked: {state['question']}"}

def route(state: State):
    return "answer" if len(state["question"]) < 5 else END

# 3. Build the graph
builder = StateGraph(State)
builder.add_node("classify", classify)
builder.add_node("answer", answer_node)

# 4. Edges
builder.add_edge(START, "classify")
builder.add_conditional_edges("classify", route)
builder.add_edge("answer", END)




# 5. Compile and run
graph = builder.compile()
import re
text = graph.get_graph().draw_mermaid()
text = re.sub(r"^---.*?---\s*", "", text, flags=re.S)
text = text.replace("<p>", "").replace("</p>", "")
print(text)
result = graph.invoke({"question": "Hiiiiiiiiiiiiiiiiiiiiiiiiiiii", "answer": ""})
print(result["answer"])

print(graph.get_graph().draw_mermaid())
print(graph.get_graph().draw_ascii())