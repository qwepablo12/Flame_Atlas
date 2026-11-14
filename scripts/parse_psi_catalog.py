"""Parse a copy-pasted PSI search results page (text) into data/psi_catalog.csv.
Usage: python scripts/parse_psi_catalog.py path/to/catalog.txt"""
import csv
import re
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
text = Path(sys.argv[1]).read_text(encoding="utf-8", errors="ignore")
blocks = re.split(r"\n(?=Investigation\s*\nPSI-\d+)", text)
rows = []
for b in blocks:
    m = re.match(r"Investigation\s*\n(PSI-\d+)\s*\n(.+?)\(\"(https://psi\.nasa\.gov[^\"]+)\"\)", b, re.S)
    if not m:
        continue
    psi_id, title, url = m.group(1), " ".join(m.group(2).split()), m.group(3)
    fields = re.search(r"Research Area\|Type\|Objectives\|Approach\|\s*\n(.+?)\|(.+?)\|(.+?)\|(.+?)\|", b, re.S)
    hi = re.search(r"Highlights:\s*(.+?)(?:\nimage\.png|\Z)", b, re.S)
    rows.append({
        "psi_id": psi_id, "title": title, "url": url,
        "research_area": fields.group(1).strip() if fields else "",
        "type": fields.group(2).strip() if fields else "",
        "objectives": " ".join(fields.group(3).split()) if fields else "",
        "approach": " ".join(fields.group(4).split()) if fields else "",
        "highlights": " ".join(hi.group(1).split())[:400] if hi else "",
    })
out = ROOT / "data/psi_catalog.csv"
with out.open("w", newline="", encoding="utf-8") as fh:
    w = csv.DictWriter(fh, fieldnames=list(rows[0].keys()))
    w.writeheader()
    w.writerows(rows)
print(f"{len(rows)} investigations -> {out}")
