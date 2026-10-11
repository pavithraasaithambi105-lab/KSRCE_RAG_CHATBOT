from collections import Counter
from pathlib import Path
from typing import List, Tuple

from app.config import settings
from app.rag.chunker import chunk_elements
from app.rag.embedder import embed_texts
from app.rag.figures import FigureDescriber
from app.rag.loader import load_pdf
from app.rag.store import VectorStore

DATA_DIR = Path(settings.data_dir)
PDF_DIR = DATA_DIR / "pdfs"
INDEX_DIR = DATA_DIR / "index"

store = VectorStore(INDEX_DIR)


def ingest_pdf(path: Path) -> dict:
    """Load -> chunk -> embed -> store one PDF. Re-ingesting the same file replaces it."""
    describer = FigureDescriber(path, INDEX_DIR / "figure_cache.json")
    elements = load_pdf(path, describer)
    chunks = chunk_elements(elements, settings.chunk_size, settings.chunk_overlap)
    if not chunks:
        raise ValueError(f"No text found in {path.name} (is it a scanned PDF?)")

    vectors = embed_texts([c.text for c in chunks])
    records = [
        {
            "id": f"{path.name}#{i}",
            "source": path.name,
            "kind": c.kind,
            "section": c.section,
            "pages": c.pages,
            "text": c.text,
        }
        for i, c in enumerate(chunks)
    ]
    store.replace_source(path.name, records, vectors)
    return {
        "source": path.name,
        "pages": max(el.page for el in elements),
        "chunks": len(chunks),
        "chunk_kinds": dict(Counter(c.kind for c in chunks)),
        "figures": describer.stats,
    }


def retrieve(question: str, k: int = settings.top_k) -> List[Tuple[dict, float]]:
    query_vector = embed_texts([question])[0]
    return store.search(question, query_vector, k)
