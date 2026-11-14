"""Table extraction with PyMuPDF, including rotated test-matrix pages."""
from __future__ import annotations

import csv
from pathlib import Path

import pymupdf


def _clean_cell(c) -> str:
    return " ".join(str(c or "").split())


def page_tables(page: pymupdf.Page) -> list[list[list[str]]]:
    """All tables on a page, with empty rows/columns removed."""
    out = []
    for t in page.find_tables().tables:
        rows = [[_clean_cell(c) for c in r] for r in t.extract()]
        rows = [r for r in rows if any(r)]
        if len(rows) < 2:
            continue
        keep = [j for j in range(len(rows[0])) if any(j < len(r) and r[j] for r in rows)]
        out.append([[r[j] if j < len(r) else "" for j in keep] for r in rows])
    return out


def to_markdown(rows: list[list[str]], max_rows: int = 200) -> str:
    head, body = rows[0], rows[1:max_rows]
    lines = ["| " + " | ".join(h or "-" for h in head) + " |", "|" + "---|" * len(head)]
    lines += ["| " + " | ".join(r) + " |" for r in body]
    return "\n".join(lines)


def document_tables(path: str | Path) -> list[dict]:
    """[{page, rows}] for every table in the document."""
    found = []
    with pymupdf.open(path) as doc:
        for i, page in enumerate(doc, start=1):
            for rows in page_tables(page):
                found.append({"page": i, "rows": rows})
    return found


def dump_tables_csv(path: str | Path, out_dir: str | Path, pages: range | None = None) -> list[Path]:
    """Save each table as its own CSV (for manual checking / direct use)."""
    out_dir = Path(out_dir)
    out_dir.mkdir(parents=True, exist_ok=True)
    written = []
    with pymupdf.open(path) as doc:
        for i, page in enumerate(doc, start=1):
            if pages and i not in pages:
                continue
            for k, rows in enumerate(page_tables(page), start=1):
                f = out_dir / f"{Path(path).stem}_p{i}_t{k}.csv"
                with f.open("w", newline="", encoding="utf-8") as fh:
                    csv.writer(fh).writerows(rows)
                written.append(f)
    return written
