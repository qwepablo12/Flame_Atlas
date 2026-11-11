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
    text = re.sub(r"-\n(\w)", r"\1", text)      # re-join hyphenated words
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


if __name__ == "__main__":
    import sys

    pages = pdf_pages(sys.argv[1])
    chunks = chunk_pages(pages)
    print(f"{len(pages)} pages, {len(chunks)} chunks")
    print(json.dumps(chunks[0], ensure_ascii=False)[:500] if chunks else "(empty — scanned PDF? needs OCR)")
