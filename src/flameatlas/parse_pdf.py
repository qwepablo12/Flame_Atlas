"""PDF -> page texts -> chunks."""
from __future__ import annotations

import json
import re
from pathlib import Path

import pymupdf


def pdf_pages(path: str | Path) -> list[str]:
    """Return the text of each page (index 0 = page 1)."""
    with pymupdf.open(path) as doc:
        return [page.get_text("text") for page in doc]


def clean(text: str) -> str:
    text = re.sub(r"-\n(\w)", r"\1", text)
    text = re.sub(r"[ \t]+", " ", text)
    text = re.sub(r"\n{3,}", "\n\n", text)
    return text.strip()


def chunk_pages(pages: list[str], max_chars: int = 3000, overlap: int = 300) -> list[dict]:
    """Split into overlapping chunks, keeping the page number of each chunk's start."""
    chunks = []
    for pno, raw in enumerate(pages, start=1):
        text = clean(raw)
        start = 0
        while start < len(text):
            end = min(start + max_chars, len(text))
            chunks.append({"page": pno, "text": text[start:end]})
            if end == len(text):
                break
            start = end - overlap
    return chunks


def document_text(pages: list[str], max_chars: int = 120_000) -> str:
    """Whole document with page markers, truncated for the LLM context."""
    parts = [f"[page {i}]\n{clean(p)}" for i, p in enumerate(pages, start=1)]
    return "\n\n".join(parts)[:max_chars]


SIGNALS = re.compile(
    r"test matrix|table \d|oxygen|O2|kPa|psi|atm\b|cm/s|mm/s|flow (velocity|speed)|extinction|"
    r"extinguish|ignit|spread rate|flammab|diluent|helium|CO2|droplet|burning rate",
    re.I,
)


def page_scores(pages: list[str]) -> list[int]:
    return [len(SIGNALS.findall(p)) for p in pages]


def select_context(pages: list[str], tables_md: dict[int, str] | None = None,
                   max_chars: int = 110_000) -> list[str]:
    """Build context windows from the intro pages, data-rich pages and tables of a long document."""
    tables_md = tables_md or {}
    full = document_text(pages, max_chars=10**9)
    if len(full) <= max_chars and not tables_md:
        return [full]

    scores = page_scores(pages)
    ranked = sorted(range(len(pages)), key=lambda i: -scores[i])
    chosen = sorted(set(range(min(3, len(pages)))) | {i for i in ranked if scores[i] >= 4})

    blocks = []
    for i in chosen:
        pno = i + 1
        if pno in tables_md:
            blocks.append(f"[page {pno} — table]\n{tables_md[pno]}")
        else:
            blocks.append(f"[page {pno}]\n{clean(pages[i])}")
    for pno, md in tables_md.items():
        if pno - 1 not in chosen:
            blocks.append(f"[page {pno} — table]\n{md}")

    windows, cur = [], ""
    for b in blocks:
        if cur and len(cur) + len(b) > max_chars:
            windows.append(cur)
            cur = ""
        cur += b[:max_chars] + "\n\n"
    if cur:
        windows.append(cur)
    return windows


if __name__ == "__main__":
    import sys

    pages = pdf_pages(sys.argv[1])
    chunks = chunk_pages(pages)
    print(f"{len(pages)} pages, {len(chunks)} chunks")
    print(json.dumps(chunks[0], ensure_ascii=False)[:500] if chunks else "(empty — scanned PDF? needs OCR)")
