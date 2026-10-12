"""Day 24: reproducible 30-case benchmark and regression gate.

Offline mode tests a deterministic fixture adapter, NOT a live model.
Live mode invokes the existing Day 10 RAG pipeline for RAG cases;
tool cases require a separately supplied integration and are marked unsupported.
"""
import argparse
import json
import math
import statistics
import sys
import time
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
DATA = Path(__file__).with_name("day24_cases.json")
BASELINE = Path(__file__).with_name("day24_baseline.json")
REPORT = ROOT / "artifacts" / "day24_report.json"
THRESHOLDS = {"routing_accuracy": 0.90, "retrieval_hit_at_5": 0.85, "citation_rate": 0.85, "tool_success": 0.90}


def load_cases(path=DATA):
    cases = json.loads(Path(path).read_text())
    ids = [c["id"] for c in cases]
    if len(cases) != 30 or len(ids) != len(set(ids)):
        raise ValueError("Day 24 requires exactly 30 uniquely identified cases")
    return cases


def fixture_result(case):
    """A stable, explicitly synthetic adapter for testing eval plumbing."""
    docs = case.get("expected_doc_ids", [])
    tool = case.get("expected_tool")
    return {"route": case["expected_route"], "retrieved_doc_ids": docs[:5],
            "citations": docs[:1] if docs else [], "tool": tool,
            "tool_ok": bool(tool), "latency_ms": 0.0, "supported": True}


def live_rag_result(case, retrieve, ask):
    if case["expected_route"] == "tool":
        return {"supported": False, "reason": "Live tool evaluator not wired"}
    start = time.perf_counter()
    chunks = retrieve(case["question"], case["tenant_id"], 5)
    answer = ask(case["question"], case["tenant_id"])
    sources = answer.get("sources", [])
    doc_ids = [x.get("doc_id") for x in chunks if isinstance(x, dict)]
    cited = [x.get("doc_id") for x in sources if isinstance(x, dict)]
    return {"route": "rag", "retrieved_doc_ids": doc_ids[:5],
            "citations": cited, "tool": None, "tool_ok": False,
            "latency_ms": round((time.perf_counter()-start)*1000,2), "supported": True}


def evaluate(cases, adapter):
    entries=[]
    for case in cases:
        try:
            out=adapter(case)
            if not out.get("supported", True):
                entries.append({"id":case["id"],"supported":False,"reason":out.get("reason","unsupported")})
                continue
            expected_docs=set(case.get("expected_doc_ids", []))
            retrieved=set(out.get("retrieved_doc_ids",[])[:5])
            citations=set(out.get("citations",[]))
            route_ok=out.get("route")==case["expected_route"]
            hit=bool(expected_docs & retrieved) if expected_docs else None
            citation_ok=bool(citations & expected_docs) if case.get("expected_citation") else None
            tool_ok=(out.get("tool")==case["expected_tool"] and out.get("tool_ok") is True) if case.get("expected_tool") else None
            latency = float(out.get("latency_ms", 0))
            if not math.isfinite(latency) or latency < 0:
                raise ValueError("Invalid latency measurement")
            entries.append({"id":case["id"],"supported":True,"routing_correct":route_ok,
                "retrieval_hit_at_5":hit,"citation_correct":citation_ok,"tool_success":tool_ok,
                "latency_ms":latency})
        except Exception as exc:
            entries.append({"id":case["id"],"supported":True,"routing_correct":False,
                "retrieval_hit_at_5":False if case.get("expected_doc_ids") else None,
                "citation_correct":False if case.get("expected_citation") else None,
                "tool_success":False if case.get("expected_tool") else None,
                "latency_ms":None,"error_type":type(exc).__name__})
    return entries


def summarize(entries):
    supported=[e for e in entries if e["supported"]]
    def metric(field):
        vals=[e[field] for e in supported if e.get(field) is not None]
        return round(sum(vals)/len(vals),4) if vals else None
    times=sorted(e["latency_ms"] for e in supported if e.get("latency_ms") is not None)
    p95=times[max(0,__import__('math').ceil(.95*len(times))-1)] if times else None
    return {"total_cases":len(entries),"evaluated_cases":len(supported),
        "unsupported_cases":len(entries)-len(supported),
        "routing_accuracy":metric("routing_correct"),"retrieval_hit_at_5":metric("retrieval_hit_at_5"),
        "citation_rate":metric("citation_correct"),"tool_success":metric("tool_success"),
        "latency_ms":{"median":statistics.median(times) if times else None,"p95":p95},
        "failed_ids":[e["id"] for e in supported if any(e.get(k) is False for k in ("routing_correct","retrieval_hit_at_5","citation_correct","tool_success"))]}


def gate(summary, baseline, thresholds=THRESHOLDS):
    failures=[]
    if summary["unsupported_cases"]:
        failures.append(f"{summary['unsupported_cases']} unsupported cases")
    for key, minimum in thresholds.items():
        score=summary.get(key)
        if score is None or score < minimum:
            failures.append(f"{key}: {score} < {minimum}")
        prior=baseline.get(key)
        if prior is not None and (score is None or score < prior-0.05):
            failures.append(f"{key}: regression vs baseline {prior}")
    # latency guardrail only when both runs measure a nonzero p95
    current=summary["latency_ms"]["p95"]
    old=baseline.get("latency_ms",{}).get("p95")
    if old and current is not None and current > old*1.5:
        failures.append(f"p95 latency: {current}ms > 1.5x baseline {old}ms")
    return failures


def main(argv=None):
    parser=argparse.ArgumentParser()
    parser.add_argument("--mode",choices=["fixture","live"],default="fixture")
    parser.add_argument("--report",type=Path,default=REPORT)
    parser.add_argument("--baseline",type=Path,default=BASELINE)
    args=parser.parse_args(argv)
    cases=load_cases()
    if args.mode=="fixture":
        adapter=fixture_result
    else:
        from app.model_adapter import OllamaAdapter
        from app.rag import ask_question
        from app.retrieval import make_retriever
        retriever=make_retriever()
        model=OllamaAdapter()
        chat=lambda messages: model.chat(messages).get("content","")
        adapter=lambda case: live_rag_result(case,retriever,lambda q,t:ask_question(q,t,retriever,chat))
    entries=evaluate(cases,adapter)
    summary=summarize(entries)
    baseline=json.loads(args.baseline.read_text())
    failures=gate(summary,baseline)
    report={"mode":args.mode,"summary":summary,"gate_passed":not failures,"gate_failures":failures,"entries":entries}
    args.report.parent.mkdir(parents=True,exist_ok=True)
    args.report.write_text(json.dumps(report,indent=2)+"\n")
    print(f"DAY 24 [{args.mode}]: {summary['evaluated_cases']}/{summary['total_cases']} evaluated; gate={'PASS' if not failures else 'FAIL'}")
    print(f"Routing={summary['routing_accuracy']} retrieval@5={summary['retrieval_hit_at_5']} citations={summary['citation_rate']} tools={summary['tool_success']}")
    print(f"Report: {args.report}")
    for f in failures: print(f"  FAIL: {f}")
    return 1 if failures else 0

if __name__=="__main__":
    sys.exit(main())
