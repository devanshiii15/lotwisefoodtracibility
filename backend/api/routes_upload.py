"""CSV upload endpoint: save -> load into SQLite -> re-index into ChromaDB."""

from fastapi import APIRouter, File, Form, HTTPException, UploadFile

from utils import ingest, rag

router = APIRouter(prefix="/api", tags=["upload"])


@router.post("/upload")
async def upload_csv(
    dataset_type: str = Form(...),
    file: UploadFile = File(...),
):
    """
    Upload a CSV for one dataset type.
    dataset_type must be one of: suppliers, lots, batches, shipments, lab_reports.
    """
    if not file.filename.lower().endswith(".csv"):
        raise HTTPException(status_code=400, detail="Please upload a .csv file.")

    try:
        contents = await file.read()
        result = ingest.save_and_index(dataset_type, contents)
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc))
    except Exception as exc:  # noqa: BLE001
        raise HTTPException(status_code=500, detail=f"Upload failed: {exc}")

    return {"message": "Uploaded and indexed successfully.", **result}


@router.post("/reindex")
def reindex():
    """Rebuild the vector index from the current CSVs in data/."""
    count = rag.build_index(reset=True)
    return {"message": "Reindexed.", "documents_indexed": count}
