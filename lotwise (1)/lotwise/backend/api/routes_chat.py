"""AI Chat endpoint. Runs the LangGraph workflow and returns answer + sources."""

from fastapi import APIRouter
from pydantic import BaseModel

from agents.graph import run_chat

router = APIRouter(prefix="/api", tags=["chat"])


class ChatRequest(BaseModel):
    question: str


class Source(BaseModel):
    source: str
    dataset: str = ""
    record_id: str = ""
    text: str = ""
    score: float | None = None


class ChatResponse(BaseModel):
    answer: str
    intent: str
    sources: list[Source] = []


@router.post("/chat", response_model=ChatResponse)
def chat(req: ChatRequest):
    result = run_chat(req.question)
    # Keep only fields the frontend needs (drop the heavy trace object here).
    return {
        "answer": result["answer"],
        "intent": result["intent"],
        "sources": result.get("sources", []),
    }
