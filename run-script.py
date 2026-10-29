import sys
import json
from pdf_loader import load_pdf_text
from graph import graph



def run_analysis(doc_path, user_prompt):
    text = load_pdf_text(doc_path)
    result = graph.invoke({"report_text": text, "user_prompt": user_prompt, "metrics": None, "analysis": None, "risks": None, "report": None}) 

    print(f"\n{'='*60}")
    print(f"USER PROMPT:  {user_prompt}")
    print(f"ROUTE TAKEN:  {result['route']}")
    print(f"{'='*60}\n")

    if result.get("metrics"):
        print("── METRICS ──")
        print(json.dumps(result["metrics"], indent=2))

    if result.get("analysis"):
        print("\n── ANALYSIS ──")
        print(json.dumps(result["analysis"], indent=2))

    if result.get("risks"):
        print("\n── RISKS ──")
        print(json.dumps(result["risks"], indent=2))

    if result.get("report"):
        print("\n── REPORT ──")
        print(json.dumps(result["report"], indent=2))



doc_path = sys.argv[1]
user_prompt = sys.argv[2]

run_analysis (doc_path, user_prompt)