"""Chunk every PDF in data/sources.csv into data/processed/chunks.jsonl for Q&A search."""
from __future__ import annotations

import json
import sys
from pathlib import Path

import pandas as pd

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))
from flameatlas.parse_pdf import chunk_pages, pdf_pages


def main():
    src = pd.read_csv(ROOT / "data/sources.csv", dtype=str).fillna("")
    out = ROOT / "data/processed/chunks.jsonl"
    out.parent.mkdir(parents=True, exist_ok=True)
    n = 0
    with out.open("w", encoding="utf-8") as fh:
        for _, s in src.iterrows():
            pdf = ROOT / "data/raw" / s["local_file"]
            if not s["local_file"] or not pdf.exists():
                print(f"skip {s['local_file'] or '(no file)'}")
                continue
            for c in chunk_pages(pdf_pages(pdf), max_chars=1500, overlap=200):
                if len(c["text"]) < 200:
                    continue
                fh.write(json.dumps({"investigation": s["investigation"], "title": s["title"],
                                     "url": s["url"], "page": c["page"], "text": c["text"]},
                                    ensure_ascii=False) + "\n")
                n += 1
            print(f"OK   {s['local_file']}")
    print(f"{n} chunks -> {out}")


if __name__ == "__main__":
    main()
