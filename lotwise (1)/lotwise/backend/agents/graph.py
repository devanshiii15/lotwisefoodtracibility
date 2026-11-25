"""
LangGraph agentic workflow for LotWise.

    START
      |
      v
  [supervisor]  (intent classifier)
      |
      +-- origin        -> Origin Agent   (RAG: where did X come from?)
      +-- contamination -> Trace Agent    (structured contamination trace)
      +-- report        -> Report Agent   (recall summary for a lot)
      +-- general       -> General Agent  (any other question, RAG)
      |
      v
     END

All RAG agents share ONE retriever (utils.rag.get_retriever), so the whole
graph reads from a single vector index.
"""

import re
from typing import List, Optional, TypedDict

from langgraph.graph import END, START, StateGraph

from utils import rag, trace as trace_util
from utils.llm import complete


# ---------------------------------------------------------------------------
# Shared graph state
# ---------------------------------------------------------------------------
class AgentState(TypedDict, total=False):
    question: str            # user's question
    intent: str              # origin | contamination | report | general
    lot_id: Optional[str]    # extracted lot id, if any
    answer: str              # final text answer
    sources: List[dict]      # retrieved citations
    trace: Optional[dict]    # structured trace result (contamination/report)


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------
LOT_RE = re.compile(r"\bL\d{3,4}\b", re.IGNORECASE)


def _extract_lot_id(text: str) -> Optional[str]:
    m = LOT_RE.search(text)
    return m.group(0).upper() if m else None


CLASSIFY_PROMPT = """Classify the user's food-traceability question into exactly
one label: origin, contamination, report, or general.

- origin: about where something came from, its supplier, ingredients, or source.
- contamination: about tracing a contaminated lot/batch, recalls, or affected products.
- report: explicitly asks to generate/create a recall report or summary document.
- general: anything else.

Return ONLY the single label word.

Question: {question}
Label:"""


def _keyword_intent(question: str) -> str:
    """Fast, deterministic fallback classifier."""
    q = question.lower()
    if any(w in q for w in ["report", "recall report", "generate report", "pdf"]):
        return "report"
    if any(w in q for w in ["contaminat", "trace", "affected", "outbreak", "recall"]):
        return "contamination"
    if any(w in q for w in ["origin", "where", "supplier", "ingredient", "source", "come from", "from"]):
        return "origin"
    return "general"


# ---------------------------------------------------------------------------
# Nodes
# ---------------------------------------------------------------------------
def supervisor(state: AgentState) -> AgentState:
    """Intent classifier. Tries the LLM, falls back to keywords."""
    question = state["question"]
    label = complete(CLASSIFY_PROMPT.format(question=question)).strip().lower()

    # Keep only the recognised label; otherwise use keyword fallback.
    label = re.sub(r"[^a-z]", "", label)
    if label not in {"origin", "contamination", "report", "general"}:
        label = _keyword_intent(question)

    return {"intent": label, "lot_id": _extract_lot_id(question)}


def origin_agent(state: AgentState) -> AgentState:
    """RAG agent for origin / supplier / ingredient questions."""
    result = rag.answer_with_citations(state["question"])
    return {"answer": result["answer"], "sources": result["sources"]}


def general_agent(state: AgentState) -> AgentState:
    """RAG agent for any other question."""
    result = rag.answer_with_citations(state["question"])
    return {"answer": result["answer"], "sources": result["sources"]}


def trace_agent(state: AgentState) -> AgentState:
    """Structured contamination trace. Needs a lot id."""
    lot_id = state.get("lot_id")
    if not lot_id:
        # No lot id in the question -> fall back to RAG so we still answer.
        result = rag.answer_with_citations(state["question"])
        return {
            "answer": (
                "I could not find a lot id (e.g. L204) in your question, so here "
                "is what the records say:\n\n" + result["answer"]
            ),
            "sources": result["sources"],
        }

    tr = trace_util.trace_lot(lot_id)
    if not tr.get("found"):
        return {"answer": tr["message"], "sources": [], "trace": tr}

    answer = (
        f"Contamination trace for lot {lot_id}:\n"
        f"- Supplier: {tr['supplier'].get('name', 'Unknown')}\n"
        f"- Ingredient: {tr['ingredient']}\n"
        f"- Affected batches: {', '.join(b['batch_id'] for b in tr['batches']) or 'none'}\n"
        f"- Shipments: {', '.join(s['shipment_id'] for s in tr['shipments']) or 'none'}\n\n"
        f"{tr['summary']}"
    )
    # Build a citation from the lot record used for the trace.
    lot_record = trace_util.db.get_lot(lot_id)
    sources = []
    if lot_record:
        sources.append({
            "source": f"lots:{lot_id}",
            "dataset": "lots",
            "record_id": lot_id,
            "text": rag._row_to_text("lots", lot_record),
            "score": None,
        })
    return {"answer": answer, "sources": sources, "trace": tr}


def report_agent(state: AgentState) -> AgentState:
    """Produce a recall summary for a lot (PDF is downloaded via the API)."""
    lot_id = state.get("lot_id")
    if not lot_id:
        return {
            "answer": "Please include a lot id (e.g. 'generate a report for L204').",
            "sources": [],
        }
    tr = trace_util.trace_lot(lot_id)
    if not tr.get("found"):
        return {"answer": tr["message"], "sources": [], "trace": tr}

    answer = (
        f"Recall report ready for lot {lot_id}.\n\n{tr['summary']}\n\n"
        f"Download the PDF from the Trace Contamination page."
    )
    return {"answer": answer, "sources": [], "trace": tr}


# ---------------------------------------------------------------------------
# Routing
# ---------------------------------------------------------------------------
def route(state: AgentState) -> str:
    return state.get("intent", "general")


# ---------------------------------------------------------------------------
# Build the graph (compiled once, reused for every request)
# ---------------------------------------------------------------------------
def build_graph():
    workflow = StateGraph(AgentState)

    workflow.add_node("supervisor", supervisor)
    workflow.add_node("origin", origin_agent)
    workflow.add_node("contamination", trace_agent)
    workflow.add_node("report", report_agent)
    workflow.add_node("general", general_agent)

    workflow.add_edge(START, "supervisor")
    workflow.add_conditional_edges(
        "supervisor",
        route,
        {
            "origin": "origin",
            "contamination": "contamination",
            "report": "report",
            "general": "general",
        },
    )
    for node in ["origin", "contamination", "report", "general"]:
        workflow.add_edge(node, END)

    return workflow.compile()


_graph = None


def get_graph():
    global _graph
    if _graph is None:
        _graph = build_graph()
    return _graph


def run_chat(question: str) -> dict:
    """Entry point used by the API: run the graph for one question."""
    graph = get_graph()
    final_state = graph.invoke({"question": question})
    return {
        "answer": final_state.get("answer", "(no answer)"),
        "sources": final_state.get("sources", []),
        "intent": final_state.get("intent", "general"),
        "lot_id": final_state.get("lot_id"),
        "trace": final_state.get("trace"),
    }
