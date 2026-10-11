"""Text descriptions for figures (org charts, flowcharts, diagrams).

A chunker can only index text, so every figure is turned into a text description:
1. Curated: "<pdf name>.figures.md" next to the PDF (or in app/pdf_data/), checked by a person.
   Always preferred because vision models can misread complex charts.
2. Vision model (settings.vision_model) for figures without a curated description. Results are
   cached in data/index/figure_cache.json so each image is only paid for once.
If neither is available the figure's own text labels stay in the normal text flow.
"""
import base64
import hashlib
import json
import logging
import re
from pathlib import Path
from typing import Dict, List, Optional

import fitz

from app.config import settings
from app.llm import client

log = logging.getLogger(__name__)

CURATED_DIR = Path(__file__).resolve().parent.parent / "pdf_data"
_SECTION = re.compile(r"^##\s+Page\s+(\d+)\s*\|\s*(.+)$", re.MULTILINE)

VISION_PROMPT = """You are converting a diagram from a document into text for a search index. Nothing may be lost.
1. First line: "Diagram type: <org chart | flowchart | process diagram | grouped boxes | other>".
2. Copy every label exactly as written.
3. Org chart / hierarchy: follow the connecting lines carefully and write an indented tree (2 spaces per level),
   each child under the box it is connected to. Then list "Reporting lines:" as "<child> reports to <parent>".
4. Flowchart / process: numbered steps in arrow order; decisions as "If <condition>: <yes path>; otherwise: <no path>".
5. Grouped boxes: each box title followed by its bullet items.
6. End with "Summary:" and 2-3 plain sentences describing what the diagram shows.
Plain text only."""


class FigureDescriber:
    def __init__(self, pdf_path: Path, cache_path: Path):
        self.curated = _load_curated(pdf_path)
        self.cache_path = cache_path
        self.cache: Dict[str, str] = json.loads(cache_path.read_text()) if cache_path.exists() else {}
        self.stats = {"curated": 0, "vision": 0, "cached": 0, "failed": 0}

    def has_curated(self, page_no: int) -> bool:
        return page_no in self.curated

    def describe(self, page, area: fitz.Rect, caption: str) -> Optional[str]:
        page_no = page.number + 1
        if page_no in self.curated:
            self.stats["curated"] += 1
            return "\n\n".join(f"Figure (page {page_no}): {title}\n{body}" for title, body in self.curated[page_no])

        if not settings.vision_model:
            return None
        png = page.get_pixmap(dpi=150, clip=area).tobytes("png")
        key = hashlib.sha1(png).hexdigest()
        if key in self.cache:
            self.stats["cached"] += 1
            body = self.cache[key]
        else:
            try:
                body = _ask_vision(png, caption)
            except Exception as e:  # keep ingesting; the raw labels stay in the text instead
                log.warning("Vision description failed for page %s: %s", page_no, e)
                self.stats["failed"] += 1
                return None
            self.cache[key] = body
            self.stats["vision"] += 1
            self._save_cache()
        title = caption or "diagram"
        return f"Figure (page {page_no}): {title}\n{body}\n(Description generated automatically by {settings.vision_model}.)"

    def _save_cache(self):
        self.cache_path.parent.mkdir(parents=True, exist_ok=True)
        self.cache_path.write_text(json.dumps(self.cache, ensure_ascii=False, indent=1))


def _ask_vision(png: bytes, caption: str) -> str:
    prompt = VISION_PROMPT + (f'\nThe figure caption is: "{caption}".' if caption else "")
    image_url = "data:image/png;base64," + base64.b64encode(png).decode()
    response = client.chat.completions.create(
        model=settings.vision_model,
        max_tokens=settings.llm_max_tokens,
        messages=[{"role": "user", "content": [
            {"type": "text", "text": prompt},
            {"type": "image_url", "image_url": {"url": image_url}},
        ]}],
    )
    return response.choices[0].message.content.strip()


def _load_curated(pdf_path: Path) -> Dict[int, List[tuple]]:
    """Parse "## Page <n> | <title>" sections from <pdf stem>.figures.md."""
    name = pdf_path.stem + ".figures.md"
    for folder in (pdf_path.parent, CURATED_DIR):
        path = folder / name
        if path.exists():
            break
    else:
        return {}

    text = re.sub(r"<!--.*?-->", "", path.read_text(), flags=re.DOTALL)
    matches = list(_SECTION.finditer(text))
    curated: Dict[int, List[tuple]] = {}
    for i, m in enumerate(matches):
        end = matches[i + 1].start() if i + 1 < len(matches) else len(text)
        body = text[m.end():end].strip()
        curated.setdefault(int(m.group(1)), []).append((m.group(2).strip(), body))
    return curated
