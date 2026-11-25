"""
RAG pipeline for LotWise.

Flow:
    CSV records -> natural-language Documents -> chunking (SentenceSplitter)
    -> embeddings (all-MiniLM-L6-v2) -> ChromaDB -> Retriever -> LLM (+ citations)

We build one shared VectorStoreIndex. Every LangGraph agent uses the SAME
retriever returned by `get_retriever()`.
"""

import csv
import os
from typing import Any, Dict, List

import chromadb
from llama_index.core import (
    Document,
    Settings,
    StorageContext,
    VectorStoreIndex,
)
from llama_index.core.node_parser import SentenceSplitter
from llama_index.embeddings.huggingface import HuggingFaceEmbedding
from llama_index.vector_stores.chroma import ChromaVectorStore

from utils.llm import complete

# Paths
BACKEND_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
PROJECT_DIR = os.path.dirname(BACKEND_DIR)
DATA_DIR = os.path.join(PROJECT_DIR, "data")
CHROMA_DIR = os.path.join(PROJECT_DIR, "chromadb")
COLLECTION_NAME = "lotwise_docs"

EMBED_MODEL_NAME = "sentence-transformers/all-MiniLM-L6-v2"

# Module-level singletons
_index: VectorStoreIndex | None = None
_retriever = None
_chroma_client = None


# ---------------------------------------------------------------------------
# 1. Document loading: turn each CSV row into a readable sentence + metadata
# ---------------------------------------------------------------------------
def _row_to_text(dataset: str, row: Dict[str, str]) -> str:
    if dataset == "suppliers":
        return (
            f"Supplier {row['supplier_id']} is {row['name']}, located in "
            f"{row['city']}, {row['country']}. It supplies {row['ingredient_supplied']}. "
            f"Contact: {row['contact_email']}. Rating: {row['rating']}."
        )
    if dataset == "lots":
        return (
            f"Lot {row['lot_id']} contains the ingredient {row['ingredient']}, "
            f"supplied by supplier {row['supplier_id']}. Quantity: "
            f"{row['quantity_kg']} kg. Received on {row['received_date']}. "
            f"Status: {row['status']}."
        )
    if dataset == "batches":
        return (
            f"Batch {row['batch_id']} is the product '{row['product_name']}', "
            f"produced from lot {row['lot_id']} at {row['facility']} on "
            f"{row['production_date']}. Quantity: {row['quantity_units']} units."
        )
    if dataset == "shipments":
        return (
            f"Shipment {row['shipment_id']} carried batch {row['batch_id']} via "
            f"{row['distributor']} to {row['destination']} on {row['ship_date']}. "
            f"Status: {row['status']}."
        )
    if dataset == "lab_reports":
        return (
            f"Lab report {row['report_id']} tested lot {row['lot_id']} for "
            f"{row['test_type']} on {row['test_date']}. Result: {row['result']}. "
            f"Status: {row['status']}."
        )
    return ", ".join(f"{k}: {v}" for k, v in row.items())


def _id_field(dataset: str) -> str:
    return {
        "suppliers": "supplier_id",
        "lots": "lot_id",
        "batches": "batch_id",
        "shipments": "shipment_id",
        "lab_reports": "report_id",
    }[dataset]


def _load_documents_from_csv(csv_path: str, dataset: str) -> List[Document]:
    if not os.path.exists(csv_path):
        return []
    docs: List[Document] = []
    with open(csv_path, newline="", encoding="utf-8") as f:
        for row in csv.DictReader(f):
            text = _row_to_text(dataset, row)
            record_id = row.get(_id_field(dataset), "")
            docs.append(
                Document(
                    text=text,
                    metadata={
                        "dataset": dataset,
                        "record_id": record_id,
                        "source": f"{dataset}:{record_id}",
                    },
                )
            )
    return docs


def load_all_documents() -> List[Document]:
    datasets = ["suppliers", "lots", "batches", "shipments", "lab_reports"]
    docs: List[Document] = []
    for ds in datasets:
        path = os.path.join(DATA_DIR, f"{ds}.csv")
        docs.extend(_load_documents_from_csv(path, ds))
    return docs


# ---------------------------------------------------------------------------
# 2. Index construction (embeddings + ChromaDB) with a shared retriever
# ---------------------------------------------------------------------------
def _configure_settings() -> None:
    """Set the embedding model + chunking globally for LlamaIndex."""
    Settings.embed_model = HuggingFaceEmbedding(model_name=EMBED_MODEL_NAME)
    Settings.node_parser = SentenceSplitter(chunk_size=256, chunk_overlap=20)
    # We call the LLM ourselves (for citation control), so disable LlamaIndex's.
    Settings.llm = None


def _get_chroma_collection():
    global _chroma_client
    if _chroma_client is None:
        os.makedirs(CHROMA_DIR, exist_ok=True)
        _chroma_client = chromadb.PersistentClient(path=CHROMA_DIR)
    return _chroma_client.get_or_create_collection(COLLECTION_NAME)


def build_index(reset: bool = False) -> int:
    """
    Build (or rebuild) the vector index from every CSV in data/.
    Returns the number of documents indexed.
    """
    global _index, _retriever
    _configure_settings()

    if reset:
        client = chromadb.PersistentClient(path=CHROMA_DIR)
        try:
            client.delete_collection(COLLECTION_NAME)
        except Exception:  # noqa: BLE001 - collection may not exist yet
            pass

    collection = _get_chroma_collection()
    vector_store = ChromaVectorStore(chroma_collection=collection)
    storage_context = StorageContext.from_defaults(vector_store=vector_store)

    documents = load_all_documents()
    _index = VectorStoreIndex.from_documents(
        documents, storage_context=storage_context
    )
    _retriever = _index.as_retriever(similarity_top_k=4)
    return len(documents)


def ensure_index() -> None:
    """Build the index lazily if it has not been built yet."""
    global _index, _retriever
    if _retriever is not None:
        return

    _configure_settings()
    collection = _get_chroma_collection()

    if collection.count() > 0:
        # Reuse the persisted Chroma collection.
        vector_store = ChromaVectorStore(chroma_collection=collection)
        _index = VectorStoreIndex.from_vector_store(vector_store)
        _retriever = _index.as_retriever(similarity_top_k=4)
    else:
        build_index(reset=False)


def get_retriever():
    """Shared retriever used by ALL agents."""
    ensure_index()
    return _retriever


# ---------------------------------------------------------------------------
# 3. Retrieve + answer with citations
# ---------------------------------------------------------------------------
def retrieve(question: str) -> List[Dict[str, Any]]:
    """Return the top matching source chunks with metadata + score."""
    retriever = get_retriever()
    nodes = retriever.retrieve(question)
    sources = []
    for n in nodes:
        sources.append(
            {
                "source": n.node.metadata.get("source", "unknown"),
                "dataset": n.node.metadata.get("dataset", ""),
                "record_id": n.node.metadata.get("record_id", ""),
                "text": n.node.get_content(),
                "score": round(float(n.score), 3) if n.score is not None else None,
            }
        )
    return sources


ANSWER_PROMPT = """You are LotWise, a food traceability assistant.
Answer the question using ONLY the context below. If the answer is not in the
context, say "I could not find that in the records." Be concise and factual.

Context:
{context}

Question: {question}

Answer:"""


def answer_with_citations(question: str) -> Dict[str, Any]:
    """RAG: retrieve sources, ground the LLM on them, return answer + sources."""
    sources = retrieve(question)
    if not sources:
        return {
            "answer": "I could not find any relevant records for that question.",
            "sources": [],
        }
    context = "\n".join(f"- {s['text']}" for s in sources)
    prompt = ANSWER_PROMPT.format(context=context, question=question)
    answer = complete(prompt)
    return {"answer": answer, "sources": sources}
