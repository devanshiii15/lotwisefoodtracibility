"""
LotWise backend - FastAPI application entrypoint.

Run:  uvicorn main:app --reload

On startup we:
  1. create the SQLite tables and load the sample CSVs (if the DB is empty)
  2. build the ChromaDB vector index (lazily on first use)
"""

import os

from dotenv import load_dotenv
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

load_dotenv()  # read backend/.env if present

from api import routes_chat, routes_dashboard, routes_trace, routes_upload  # noqa: E402
from utils import db  # noqa: E402

app = FastAPI(title="LotWise API", version="1.0.0")

# Allow the Next.js dev server to call the API.
FRONTEND_ORIGIN = os.getenv("FRONTEND_ORIGIN", "http://localhost:3000")
app.add_middleware(
    CORSMiddleware,
    allow_origins=[FRONTEND_ORIGIN, "http://127.0.0.1:3000"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Register routers
app.include_router(routes_dashboard.router)
app.include_router(routes_chat.router)
app.include_router(routes_trace.router)
app.include_router(routes_upload.router)


@app.on_event("startup")
def on_startup():
    # Create tables and seed from data/ CSVs if the suppliers table is empty.
    db.init_db()
    if db.table_count("suppliers") == 0:
        counts = db.seed_from_csv_dir()
        print("Seeded SQLite from CSVs:", counts)
    else:
        print("SQLite already has data; skipping seed.")
    # Note: the vector index is built lazily on the first chat/trace request
    # so startup stays fast. Call POST /api/reindex to force a rebuild.


@app.get("/")
def root():
    return {"name": "LotWise API", "status": "ok", "docs": "/docs"}


@app.get("/api/health")
def health():
    return {"status": "healthy"}
