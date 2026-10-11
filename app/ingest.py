"""Index PDFs from the command line: python -m app.ingest path/to/file.pdf [more.pdf ...]"""
import json
import sys
from pathlib import Path

from app.rag.pipeline import ingest_pdf


def main():
    if len(sys.argv) < 2:
        sys.exit("usage: python -m app.ingest <file.pdf> [more.pdf ...]")
    for arg in sys.argv[1:]:
        print(json.dumps(ingest_pdf(Path(arg)), indent=2))


if __name__ == "__main__":
    main()
