from pathlib import Path

from fastapi import APIRouter, File, HTTPException, UploadFile
from openai import OpenAIError

from app.rag.pipeline import PDF_DIR, ingest_pdf, store
from app.schemas import IngestResponse

router = APIRouter(prefix="/documents", tags=["documents"])


@router.post("", response_model=IngestResponse)
def upload_pdf(file: UploadFile = File(...)):
    name = Path(file.filename or "").name
    if not name.lower().endswith(".pdf"):
        raise HTTPException(status_code=400, detail="Only .pdf files are supported.")
    PDF_DIR.mkdir(parents=True, exist_ok=True)
    path = PDF_DIR / name
    path.write_bytes(file.file.read())
    try:
        return ingest_pdf(path)
    except ValueError as e:
        raise HTTPException(status_code=422, detail=str(e))
    except OpenAIError as e:
        raise HTTPException(status_code=502, detail=f"Embedding error: {e}")


@router.get("")
def list_documents():
    """Indexed documents and how many chunks each has."""
    return store.sources()


@router.delete("/{name}")
def delete_document(name: str):
    removed = store.remove_source(name)
    if not removed:
        raise HTTPException(status_code=404, detail=f"{name} is not indexed.")
    (PDF_DIR / Path(name).name).unlink(missing_ok=True)
    return {"source": name, "chunks_removed": removed}
