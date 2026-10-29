import json
import sys
import math
from pdf_loader import load_pdf_text
from graph import graph


# ─── Value comparison ─────────────────────────────────────────

def values_match(expected, actual) -> bool:
    """
    Compares expected vs actual with tolerance for floats.
    None == None → True
    Float tolerance: 1.0 for large numbers, 0.05 for small
    String: lowercase + strip comparison
    """
    if expected is None or actual is None:
        return expected is None and actual is None

    if isinstance(expected, (int, float)) and isinstance(actual, (int, float)):
        if math.isnan(float(expected)) and math.isnan(float(actual)):
            return True
        tolerance = 1.0 if abs(expected) >= 100 else 0.05
        return abs(expected - actual) <= tolerance

    return str(expected).strip().lower() == str(actual).strip().lower()


# ─── Section checkers ─────────────────────────────────────────

def check_metrics(expected: dict, actual: dict) -> tuple[int, int]:
    passed = 0
    total  = 0

    for field, exp_value in expected.items():
        total += 1
        act_value = actual.get(field)
        ok = values_match(exp_value, act_value)
        if ok:
            passed += 1
        status = "PASS" if ok else "FAIL"
        print(f"  {status}  metrics.{field}: expected={exp_value!r} actual={act_value!r}")

    return passed, total


def check_analysis(expected: dict, actual: dict) -> tuple[int, int]:
    passed = 0
    total  = 0

    # Check net_margin_percent
    total += 1
    exp = expected.get("net_margin_percent")
    act = actual.get("net_margin_percent")
    ok  = values_match(exp, act)
    if ok:
        passed += 1
    print(f"  {'PASS' if ok else 'FAIL'}  analysis.net_margin_percent: expected={exp!r} actual={act!r}")

    # Check computed values
    exp_computed = expected.get("computed", {})
    act_computed = actual.get("computed", {})

    for field, exp_value in exp_computed.items():
        total += 1
        act_value = act_computed.get(field)
        ok = values_match(exp_value, act_value)
        if ok:
            passed += 1
        status = "PASS" if ok else "FAIL"
        print(f"  {status}  analysis.computed.{field}: expected={exp_value!r} actual={act_value!r}")

    return passed, total


def check_risks(expected: dict, actual: list) -> tuple[int, int]:
    passed = 0
    total  = 3  # three structural checks

    # Check minimum count
    min_count = expected.get("minimum_count", 2)
    actual_count = len(actual) if actual else 0
    ok = actual_count >= min_count
    if ok:
        passed += 1
    print(f"  {'PASS' if ok else 'FAIL'}  risks.minimum_count: expected>={min_count} actual={actual_count}")

    # Check all evidence verified
    if actual:
        all_verified = all(r.get("evidence_verified") for r in actual)
    else:
        all_verified = False
    ok = all_verified == expected.get("all_verified", True)
    if ok:
        passed += 1
    print(f"  {'PASS' if ok else 'FAIL'}  risks.all_verified: expected={expected.get('all_verified')} actual={all_verified}")

    # Check no table rows in evidence
    def is_table_row(text: str) -> bool:
        import re
        if len(re.findall(r"\$[\d,]+", text)) >= 2:
            return True
        if len(re.findall(r"\(\d+\)", text)) >= 2:
            return True
        digits = len(re.findall(r"\d", text))
        return digits / len(text) > 0.35 if text else False

    if actual:
        no_table_rows = not any(
            is_table_row(r.get("evidence", ""))
            for r in actual
        )
    else:
        no_table_rows = False

    ok = no_table_rows == expected.get("no_table_rows", True)
    if ok:
        passed += 1
    print(f"  {'PASS' if ok else 'FAIL'}  risks.no_table_rows: expected={expected.get('no_table_rows')} actual={no_table_rows}")

    return passed, total


def check_report(expected: dict, actual: dict) -> tuple[int, int]:
    passed = 0
    total  = 1

    exp_verdict = expected.get("verdict")
    act_verdict = actual.get("verdict") if actual else None
    ok = values_match(exp_verdict, act_verdict)
    if ok:
        passed += 1
    print(f"  {'PASS' if ok else 'FAIL'}  report.verdict: expected={exp_verdict!r} actual={act_verdict!r}")

    return passed, total


# ─── Main runner ──────────────────────────────────────────────

def run_golden_check(pdf_path: str, golden_path: str):
    print(f"\n{'='*60}")
    print(f"GOLDEN SET EVALUATION")
    print(f"PDF:    {pdf_path}")
    print(f"Golden: {golden_path}")
    print(f"{'='*60}\n")

    # Load golden dataset
    with open(golden_path, encoding="utf-8") as f:
        golden = json.load(f)

    # Load PDF and run full analysis
    print("Running full_analysis pipeline...\n")
    text = load_pdf_text(pdf_path)

    result = graph.invoke({
        "report_text": text,
        "user_prompt": "give me the complete analysis",
        "route":       None,
        "metrics":     None,
        "analysis":    None,
        "risks":       None,
        "report":      None,
    })

    total_passed = 0
    total_checks = 0

    # ── Check metrics ──
    print("── METRICS ──")
    if golden.get("metrics") and result.get("metrics"):
        p, t = check_metrics(golden["metrics"], result["metrics"])
        total_passed += p
        total_checks += t
    else:
        print("  SKIP  metrics not available")

    # ── Check analysis ──
    print("\n── ANALYSIS ──")
    if golden.get("analysis") and result.get("analysis"):
        p, t = check_analysis(golden["analysis"], result["analysis"])
        total_passed += p
        total_checks += t
    else:
        print("  SKIP  analysis not available")

    # ── Check risks ──
    print("\n── RISKS ──")
    if golden.get("risks") and result.get("risks") is not None:
        p, t = check_risks(golden["risks"], result["risks"])
        total_passed += p
        total_checks += t
    else:
        print("  SKIP  risks not available")

    # ── Check report ──
    print("\n── REPORT ──")
    if golden.get("report") and result.get("report"):
        p, t = check_report(golden["report"], result["report"])
        total_passed += p
        total_checks += t
    else:
        print("  SKIP  report not available")

    # ── Final score ──
    print(f"\n{'='*60}")
    print(f"RESULT: {total_passed}/{total_checks} checks passed")
    pct = round(total_passed / total_checks * 100, 1) if total_checks > 0 else 0
    print(f"SCORE:  {pct}%")
    print(f"{'='*60}\n")


if __name__ == "__main__":
    if len(sys.argv) < 3:
        print("Usage: python check_golden.py <pdf_path> <golden_path>")
        print("Example: python check_golden.py samples/Goldman-Q3.pdf golden_dataset.json")
        sys.exit(1)

    run_golden_check(sys.argv[1], sys.argv[2])