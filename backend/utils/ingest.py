"""
Handle CSV uploads.

Steps when a file is uploaded:
    1. Save it into data/<type>.csv   (overwrites the sample file)
    2. Load the rows into SQLite
    3. Rebuild the ChromaDB vector index so new records are searchable
"""

import os

from utils import db, rag

DATA_DIR = db.DATA_DIR

VALID_TYPES = set(db.TABLES.keys())  # suppliers, lots, batches, shipments, lab_reports


def save_and_index(dataset_type: str, file_bytes: bytes) -> dict:
    if dataset_type not in VALID_TYPES:
        raise ValueError(
            f"Invalid type '{dataset_type}'. Must be one of {sorted(VALID_TYPES)}."
        )

    os.makedirs(DATA_DIR, exist_ok=True)
    save_path = os.path.join(DATA_DIR, f"{dataset_type}.csv")
    with open(save_path, "wb") as f:
        f.write(file_bytes)

    # Load into SQLite
    rows_loaded = db.load_uploaded_csv(save_path, dataset_type)

    # Rebuild the vector index so the new rows are retrievable
    docs_indexed = rag.build_index(reset=True)

    return {
        "type": dataset_type,
        "rows_loaded": rows_loaded,
        "documents_indexed": docs_indexed,
    }
