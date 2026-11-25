# 🌿 LotWise — AI Food Traceability Assistant

LotWise answers questions about food batches and traces contaminated lots using
sample supplier records, batch records, and laboratory reports.

It is a **college demonstration project** built to showcase:

- **LLMs** (Ollama + Qwen3)
- **Retrieval Augmented Generation (RAG)** (LlamaIndex + ChromaDB + MiniLM embeddings)
- **LangGraph** agentic workflow (supervisor → intent classifier → agents)
- **FastAPI** backend
- **Next.js** frontend (TypeScript, Tailwind, shadcn/ui, React Flow)

---

## ✨ Features

| Feature | What it does |
|---|---|
| **Dashboard** | Counts of suppliers, batches, lots & lab alerts + charts |
| **AI Chat** | Ask questions; answers are grounded in retrieved documents with **citations** |
| **Trace Contamination** | Enter a lot → auto-trace Supplier → Ingredient → Batches → Shipments → Recall Summary (text + flowchart + graph) |
| **CSV Upload** | Upload suppliers/lots/batches/shipments/lab reports → auto-indexed into ChromaDB |
| **Supply Chain Graph** | Interactive React Flow visualization |
| **Recall Report** | Downloadable PDF (lot, supplier, batches, summary, timestamp) |

---

## 🏗️ Architecture

```
                         ┌─────────────────────────────┐
   Next.js Frontend  ──▶ │  FastAPI  (main.py)         │
   (Dashboard, Chat,     │                             │
    Trace, Upload)       │  ┌────────────────────────┐ │
                         │  │ LangGraph workflow      │ │
                         │  │  supervisor (intent)    │ │
                         │  │   ├─ origin  (RAG)      │ │
                         │  │   ├─ contamination      │ │
                         │  │   ├─ report             │ │
                         │  │   └─ general (RAG)      │ │
                         │  └────────┬───────────────┘ │
                         │           │ shared retriever │
                         │  ┌────────▼───────────────┐ │
                         │  │ RAG: LlamaIndex         │ │
                         │  │ MiniLM → ChromaDB       │ │
                         │  └─────────────────────────┘ │
                         │  ┌─────────────────────────┐ │
                         │  │ SQLite (structured trace)│ │
                         │  └─────────────────────────┘ │
                         │  ┌─────────────────────────┐ │
                         │  │ Ollama Qwen3 (LLM)      │ │
                         │  └─────────────────────────┘ │
                         └─────────────────────────────┘
```

**Design note:** structured questions (contamination trace) use **SQLite** for exact,
reproducible relationships. Open-ended questions use the **RAG** pipeline. Each tool
is used where it's strongest.

---

## 📂 Project structure

```
lotwise/
├── backend/
│   ├── main.py                # FastAPI app
│   ├── agents/
│   │   └── graph.py           # LangGraph workflow (supervisor + agents)
│   ├── api/                   # API routes (dashboard, chat, trace, upload)
│   ├── utils/
│   │   ├── db.py              # SQLite
│   │   ├── rag.py             # RAG pipeline (LlamaIndex + ChromaDB)
│   │   ├── llm.py             # Ollama Qwen3 wrapper
│   │   ├── trace.py           # deterministic contamination trace
│   │   ├── ingest.py          # CSV upload + reindex
│   │   └── pdf_report.py      # recall report PDF
│   ├── requirements.txt
│   └── .env.example
├── frontend/                  # Next.js + TypeScript + Tailwind + shadcn/ui
│   ├── app/                   # dashboard, chat, trace, upload, about
│   ├── components/            # sidebar, stat-card, supply-chain-graph, ui/
│   ├── lib/api.ts             # API client
│   └── package.json
├── data/                      # sample CSVs (suppliers, lots, batches, shipments, lab_reports)
├── scripts/generate_data.py   # regenerate sample data
├── chromadb/                  # vector store (created on first run)
└── README.md
```

---

## 🚀 Setup

### Prerequisites
- **Python 3.10+**
- **Node.js 18+**
- **Ollama** installed and running — https://ollama.com

Pull the model:
```bash
ollama pull qwen3
```

### 1) Backend

```bash
cd backend
python -m venv venv
# Windows: venv\Scripts\activate
source venv/bin/activate

pip install -r requirements.txt

cp .env.example .env        # optional; defaults work out of the box
uvicorn main:app --reload
```

Backend runs at **http://localhost:8000** (API docs at `/docs`).
On first start it loads the sample CSVs into SQLite. The vector index builds
lazily on the first chat/trace request (first run downloads the MiniLM model).

### 2) Frontend

```bash
cd frontend
npm install
cp .env.local.example .env.local   # optional; defaults to localhost:8000
npm run dev
```

Frontend runs at **http://localhost:3000**.

---

## 🎬 Demo script (for the presentation)

1. **Dashboard** — show the counts and charts.
2. **AI Chat** — ask *“Where did Batch B180 originate?”* Point out the **sources** shown below the answer.
3. **Trace Contamination** — enter **`L204`** (the seeded contaminated lot).
   Show the flowchart, the recall summary, the React Flow graph, and download the **PDF**.
4. **Upload CSV** — re-upload `data/lab_reports.csv` to show auto-indexing.
5. **About** — explain RAG, LangGraph, and the SQLite-vs-RAG split.

> The sample data seeds **Lot L204** (Romaine Lettuce, GreenFields Farms, E. coli positive)
> as a ready-made contamination scenario.

---

## 🔧 Regenerate sample data (optional)

```bash
cd scripts
python generate_data.py
```

Then restart the backend (delete `backend/lotwise.db` first to reseed) and click
**Reindex** via `POST /api/reindex` or re-upload the CSVs.

---

## 🧠 Where each concept lives

| Concept | File |
|---|---|
| LLM | `backend/utils/llm.py` |
| RAG (loader→chunk→embed→Chroma→retriever) | `backend/utils/rag.py` |
| LangGraph workflow | `backend/agents/graph.py` |
| Agentic routing | `supervisor` node in `graph.py` |
| Structured trace | `backend/utils/trace.py` |
| PDF report | `backend/utils/pdf_report.py` |
| React Flow graph | `frontend/components/supply-chain-graph.tsx` |
