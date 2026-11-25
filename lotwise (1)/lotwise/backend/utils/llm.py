"""
Thin wrapper around the Ollama LLM (Qwen3).

We keep a single shared LlamaIndex Ollama client so every agent uses the same
model configuration. If Ollama is not running we return a clear message instead
of crashing the whole request - useful during a live demo.
"""

import os

from llama_index.llms.ollama import Ollama

# Configurable via .env
OLLAMA_MODEL = os.getenv("OLLAMA_MODEL", "qwen3")
OLLAMA_BASE_URL = os.getenv("OLLAMA_BASE_URL", "http://localhost:11434")
REQUEST_TIMEOUT = float(os.getenv("OLLAMA_TIMEOUT", "120"))

_llm = None


def get_llm() -> Ollama:
    """Return a shared Ollama LLM instance."""
    global _llm
    if _llm is None:
        _llm = Ollama(
            model=OLLAMA_MODEL,
            base_url=OLLAMA_BASE_URL,
            request_timeout=REQUEST_TIMEOUT,
            # Qwen3 supports a "thinking" mode; disable it for concise answers.
            additional_kwargs={"think": False},
        )
    return _llm


def complete(prompt: str) -> str:
    """
    Send a prompt to Qwen3 and return plain text.
    Never raises - returns a readable error string on failure.
    """
    try:
        resp = get_llm().complete(prompt)
        text = str(resp).strip()
        # Some Qwen3 builds wrap reasoning in <think>...</think>; strip it.
        if "<think>" in text and "</think>" in text:
            text = text.split("</think>", 1)[1].strip()
        return text or "(the model returned an empty response)"
    except Exception as exc:  # noqa: BLE001 - demo-friendly error handling
        return (
            "[LLM unavailable] Could not reach Ollama at "
            f"{OLLAMA_BASE_URL}. Make sure Ollama is running and the model "
            f"'{OLLAMA_MODEL}' is pulled (`ollama pull {OLLAMA_MODEL}`). "
            f"Details: {exc}"
        )
