"""Split document elements into chunks for embedding.

- Text is chunked per section with overlap, ending on paragraph/sentence boundaries.
- Tables and figures are kept whole (large tables are split by rows, header repeated).
- Every chunk starts with its section path, e.g. "Section: 9. ADMINISTRATIVE SET UP > 9.1 Chairman",
  so a chunk still makes sense on its own and matches searches for the section name.
"""
from bisect import bisect_right
from dataclasses import dataclass
from typing import List

from app.rag.loader import Element

# Preferred places to end a chunk, best first.
_BREAKS = ["\n\n", "\n", ". ", "? ", "! ", "; ", " "]


@dataclass
class Chunk:
    text: str
    pages: List[int]
    kind: str  # "text" | "table" | "figure"
    section: str


def chunk_elements(elements: List[Element], chunk_size: int, overlap: int) -> List[Chunk]:
    chunks: List[Chunk] = []
    path: List[str] = []  # current heading stack
    buffer: List[Element] = []  # text elements of the current section

    def section() -> str:
        return " > ".join(path)

    def flush():
        if buffer:
            chunks.extend(_chunk_text(buffer, section(), chunk_size, overlap))
            buffer.clear()

    for el in elements:
        if el.kind == "heading":
            flush()
            del path[el.level - 1:]
            path.append(el.text)
            buffer.append(el)  # keep the heading text in the section's first chunk
        elif el.kind == "text":
            buffer.append(el)
        elif el.kind == "table":
            chunks.extend(_chunk_table(el, section(), chunk_size))
        elif el.kind == "figure":
            chunks.append(Chunk(_with_header(section(), el.text), [el.page], "figure", section()))
    flush()
    return chunks


def _with_header(section: str, text: str) -> str:
    return f"Section: {section}\n{text}" if section else text


def _chunk_text(elements: List[Element], section: str, chunk_size: int, overlap: int) -> List[Chunk]:
    text = ""
    starts, pages = [], []  # character offset where each element begins, and its page
    for el in elements:
        starts.append(len(text))
        pages.append(el.page)
        text += el.text + "\n\n"

    chunks = []
    start = 0
    while start < len(text):
        end = min(start + chunk_size, len(text))
        if end < len(text):
            end = _snap_back(text, start, end)

        piece = text[start:end].strip()
        if piece:
            first = pages[bisect_right(starts, start) - 1]
            last = pages[bisect_right(starts, end - 1) - 1]
            chunks.append(Chunk(_with_header(section, piece), list(range(first, last + 1)), "text", section))

        if end >= len(text):
            break
        # Step back by `overlap`, then forward to the next word so we don't start mid-word.
        next_start = max(end - overlap, start + 1)
        space = text.find(" ", next_start, end)
        start = space + 1 if space != -1 else next_start
    return chunks


def _snap_back(text: str, start: int, end: int) -> int:
    """Move `end` back to the best boundary in the last half of the window."""
    floor = start + (end - start) // 2
    for sep in _BREAKS:
        pos = text.rfind(sep, floor, end)
        if pos != -1:
            return pos + len(sep)
    return end


def _chunk_table(el: Element, section: str, chunk_size: int) -> List[Chunk]:
    """Keep small tables whole; split big ones by rows, repeating the title and header."""
    lines = el.text.split("\n")
    sep = next((i for i, line in enumerate(lines) if line.startswith("|---")), None)
    limit = int(chunk_size * 1.5)
    if sep is None or len(el.text) <= limit:
        return [Chunk(_with_header(section, el.text), [el.page], "table", section)]

    head, rows = lines[: sep + 1], lines[sep + 1:]
    chunks, part = [], []
    for row in rows:
        if part and len("\n".join(head + part + [row])) > limit:
            chunks.append(part)
            part = []
        part.append(row)
    if part:
        chunks.append(part)
    return [
        Chunk(
            _with_header(section, "\n".join(head + part + [f"(table part {i + 1} of {len(chunks)})"])),
            [el.page], "table", section,
        )
        for i, part in enumerate(chunks)
    ]
