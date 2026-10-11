"""Turn a PDF into an ordered list of elements: headings, text, tables and figures.

Plain text extraction loses the structure that matters for RAG, so each page is split into:
- headings  -> numbered bold lines like "9.1 Chairman", used to label every chunk with its section
- tables    -> detected by PyMuPDF and written out as Markdown (header kept, page breaks merged)
- figures   -> images and drawn diagrams, replaced by a text description (see figures.py)
- text      -> everything else, in reading order, minus repeated page headers/footers
"""
import re
from collections import Counter
from dataclasses import dataclass
from pathlib import Path
from typing import List, Optional

import fitz  # PyMuPDF

from app.rag.figures import FigureDescriber

_HEADING = re.compile(r"^(\d{1,2}(?:\.\d{1,2})*)\.?\s+(\S.{0,110})$")
_CAPTION = re.compile(r"^\s*fig(?:ure)?\b[\s.\-]*", re.IGNORECASE)
_AUTO_COLUMN = re.compile(r"^Col\d+$")
_TOP_MARGIN, _BOTTOM_MARGIN = 60, 80  # points treated as header/footer zone
_LINE_GAP = 12  # text blocks closer than this (points) belong to the same paragraph


@dataclass
class Element:
    kind: str  # "heading" | "text" | "table" | "figure"
    text: str
    page: int  # 1-based
    level: int = 0  # heading depth: "9." -> 1, "9.1" -> 2


def load_pdf(path: Path, describer: FigureDescriber) -> List[Element]:
    doc = fitz.open(str(path))
    boilerplate = _repeated_lines(doc)
    elements: List[Element] = []
    last_table: Optional[dict] = None  # to stitch tables that continue onto the next page

    for page in doc:
        page_no = page.number + 1
        figure_area = _figure_area(page, describer.has_curated(page_no))
        items = []  # (sort key, Element)

        described = False
        if figure_area is not None:
            description = describer.describe(page, figure_area, _caption_near(page, figure_area))
            if description:
                described = True
                items.append((_order_key(page, figure_area), Element("figure", description, page_no)))

        tables = [t for t in page.find_tables().tables if not _inside(fitz.Rect(t.bbox), figure_area)]
        table_rects = [fitz.Rect(t.bbox) for t in tables]
        for table in tables:
            text, last_table = _table_to_text(page, table, last_table)
            if text:
                items.append((_order_key(page, fitz.Rect(table.bbox)), Element("table", text, page_no)))

        for rect, lines in _text_blocks(page):
            if any(_inside(rect, r) for r in table_rects):
                continue
            if described and _inside(rect, figure_area):
                continue  # the figure description already contains these labels
            if _is_margin(page, rect) and all(_norm(l[0]) in boilerplate or l[0].isdigit() for l in lines):
                continue
            items.extend((_order_key(page, rect), el) for el in _lines_to_elements(lines, page_no))

        items.sort(key=lambda it: it[0])
        elements.extend(_merge_lines(page, items))
    return elements


def _merge_lines(page, items) -> List[Element]:
    """Many PDFs store each printed line as its own block; join lines into paragraphs."""
    out: List[Element] = []
    prev_rect = None
    for key, el in items:
        rect = fitz.Rect(*key[2]) if len(key) > 2 else None
        if (
            el.kind == "text" and out and out[-1].kind == "text" and rect is not None
            and prev_rect is not None and -2 <= rect.y0 - prev_rect.y1 < _LINE_GAP
        ):
            out[-1].text = _join_lines([out[-1].text, el.text])
            prev_rect = prev_rect | rect
            continue
        out.append(el)
        prev_rect = rect
    return out


# ---------- text ----------

def _text_blocks(page):
    """Yield (rect, [(line_text, is_bold)]) for each text block."""
    for block in page.get_text("dict")["blocks"]:
        if block.get("type") != 0:
            continue
        lines = []
        for line in block["lines"]:
            spans = [s for s in line["spans"] if s["text"].strip()]
            if not spans:
                continue
            text = _clean("".join(s["text"] for s in line["spans"]))
            bold = all(s["flags"] & 16 or "bold" in s["font"].lower() for s in spans)
            lines.append((text, bold))
        if lines:
            yield fitz.Rect(block["bbox"]), lines


def _lines_to_elements(lines, page_no) -> List[Element]:
    out: List[Element] = []
    buf: List[str] = []
    for text, bold in lines:
        level = _heading_level(text) if bold else 0
        if level:
            if buf:
                out.append(Element("text", " ".join(buf), page_no))
                buf = []
            out.append(Element("heading", text, page_no, level))
        else:
            buf.append(text)
    if buf:
        out.append(Element("text", _join_lines(buf), page_no))
    return out


def _heading_level(text: str) -> int:
    m = _HEADING.match(text)
    if not m or text.rstrip().endswith(tuple("0123456789")) and "..." in text:
        return 0
    depth = len(m.group(1).split("."))
    if depth == 1:
        # Top-level headings are upper case ("9. ADMINISTRATIVE SET UP"); this skips bold list items.
        letters = [c for c in m.group(2) if c.isalpha()]
        if not letters or sum(c.isupper() for c in letters) / len(letters) < 0.6:
            return 0
    return depth


def _join_lines(lines: List[str]) -> str:
    """Join wrapped lines; keep bullets on their own line."""
    out = ""
    for line in lines:
        if not out:
            out = line
        elif line.startswith("•") or re.match(r"^(\(?[a-zivx\d]{1,4}[.)])\s", line):
            out += "\n" + line
        elif out.endswith("-") and line[:1].islower():
            out += line  # "extra-" + "curricular" -> "extra-curricular"
        else:
            out += " " + line
    return out


def _clean(text: str) -> str:
    text = re.sub(r"[-]", "•", text)  # Wingdings bullets (, ) -> •
    text = text.replace(" ", " ").replace("\x00", "")
    return re.sub(r"\s+", " ", text).strip()


def _norm(text: str) -> str:
    return re.sub(r"[\d\s]+", " ", text).strip().lower()


def _repeated_lines(doc) -> set:
    """Short lines found in the page margins of many pages (running headers/footers)."""
    counts: Counter = Counter()
    for page in doc:
        seen = set()
        for rect, lines in _text_blocks(page):
            if _is_margin(page, rect):
                seen.update(_norm(t) for t, _ in lines if len(t) < 60)
        counts.update(seen)
    return {line for line, n in counts.items() if line and n >= max(3, len(doc) * 0.3)}


# ---------- tables ----------

def _table_to_text(page, table, last_table: Optional[dict]):
    header = [_clean(h or "") for h in table.header.names]
    rows = [[_clean(c or "") for c in row] for row in table.extract()]
    if not table.header.external and rows:
        rows = rows[1:]

    rect = _visual(page, fitz.Rect(table.bbox))
    # A table at the top of a page with the same columns as a table that ended at the bottom
    # of the previous page is the same table continuing.
    continued = (
        last_table is not None
        and last_table["page"] == page.number  # i.e. the table ended on the previous page
        and len(last_table["header"]) == len(header)
        and rect.y0 < 120
    )
    if continued:
        if [h.lower() for h in header] != [h.lower() for h in last_table["header"]]:
            rows = [header] + rows  # no repeated header: the first row is data
        header = last_table["header"]
    header = ["" if _AUTO_COLUMN.match(h) else h for h in header]
    full_header = header

    cleaned = []
    for row in rows:
        if row == header or (cleaned and row == cleaned[-1]) or not any(row):
            continue
        cleaned.append(row)
    keep = [i for i in range(len(header)) if header[i] or any(r[i] for r in cleaned)]
    header = [header[i] for i in keep]
    cleaned = [[r[i] for i in keep] for r in cleaned]

    page_rect = page.rect
    at_bottom = rect.y1 > page_rect.height - 150
    new_last = {"page": page.number + 1, "header": full_header} if at_bottom else None
    if not cleaned and not any(header):
        return "", new_last

    title = "" if continued else _text_above(page, fitz.Rect(table.bbox))
    lines = []
    if continued:
        lines.append(f"(Table continued from page {page.number})")
    elif title:
        lines.append(f"Table: {title}")
    lines.append("| " + " | ".join(h or " " for h in header) + " |")
    lines.append("|" + "---|" * len(header))
    lines.extend("| " + " | ".join(r) + " |" for r in cleaned)
    return "\n".join(lines), new_last


def _text_above(page, rect: fitz.Rect) -> str:
    """The text line just above a table, usually its title."""
    best, best_gap = "", 40.0
    target = _visual(page, rect)
    for block_rect, lines in _text_blocks(page):
        r = _visual(page, block_rect)
        gap = target.y0 - r.y1
        if 0 <= gap < best_gap and r.x1 > target.x0 and r.x0 < target.x1:
            best, best_gap = lines[-1][0], gap
    return best


# ---------- figures ----------

def _figure_area(page, curated: bool) -> Optional[fitz.Rect]:
    """Region covered by images or drawn diagrams on this page, or None.

    Images: any picture larger than 5% of the page (small logos/icons are skipped).
    Drawn diagrams: shapes outside tables, only on pages with a "Figure" caption or a curated
    description (otherwise table borders and underlines would look like diagrams).
    """
    page_area = _area(page.rect)
    area = None
    for img in page.get_images(full=True):
        for r in page.get_image_rects(img[0]):
            if _area(r) > 0.05 * page_area:
                area = fitz.Rect(r) if area is None else area | r

    if area is None and (curated or _caption_near(page, None)):
        tables = [fitz.Rect(t.bbox) for t in page.find_tables().tables] if not curated else []
        for d in page.get_drawings():
            r = fitz.Rect(d["rect"])
            if r.width > page.rect.width * 0.8 and r.height > page.rect.height * 0.8:
                continue  # page border
            if _is_margin(page, r) or any(_inside(r, t) for t in tables):
                continue
            area = fitz.Rect(r) if area is None else area | r
        if area is not None and _area(area) < 0.05 * page_area:
            area = None
    if area is not None and page.number == 0 and not curated:
        return None  # cover page artwork (logo, campus photo)
    return area


def _caption_near(page, area: Optional[fitz.Rect]) -> str:
    """A "Figure ..." caption on the page (closest to `area` if given)."""
    best, best_dist = "", float("inf")
    for rect, lines in _text_blocks(page):
        text = " ".join(t for t, _ in lines)
        if _CAPTION.match(text) and len(text) < 160:
            dist = 0 if area is None else abs(_visual(page, rect).y0 - _visual(page, area).y1)
            if dist < best_dist:
                best, best_dist = text, dist
    return best


# ---------- geometry ----------

def _visual(page, rect: fitz.Rect) -> fitz.Rect:
    """Rect in the page's displayed orientation (handles landscape/rotated pages)."""
    return rect * page.rotation_matrix if page.rotation else rect


def _order_key(page, rect: fitz.Rect):
    r = _visual(page, rect)
    return (round(r.y0 / 4), r.x0, tuple(r))


def _is_margin(page, rect: fitz.Rect) -> bool:
    r = _visual(page, rect)
    return r.y1 < _TOP_MARGIN or r.y0 > page.rect.height - _BOTTOM_MARGIN


def _inside(rect: fitz.Rect, outer: Optional[fitz.Rect]) -> bool:
    if outer is None:
        return False
    return _area(rect & outer) >= 0.7 * max(_area(rect), 1.0)


def _area(rect: fitz.Rect) -> float:
    return max(rect.width, 0) * max(rect.height, 0) if not rect.is_empty else 0.0

