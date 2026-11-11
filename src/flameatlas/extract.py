"""LLM extraction: document text -> list[TestRecord].

Uses Claude tool use with a forced tool call so the answer is always valid JSON
matching the schema. Results are cached per file, so re-runs cost nothing.
"""
from __future__ import annotations

import hashlib
import json
import os
from pathlib import Path

import anthropic
from dotenv import load_dotenv

from .parse_pdf import document_text, pdf_pages, select_context
from .schema import ExtractionResult, TestRecord
from .tables import document_tables, to_markdown

load_dotenv()

MODEL = os.getenv("FLAMEATLAS_MODEL", "claude-sonnet-5-5")
CACHE_DIR = Path(os.getenv("FLAMEATLAS_CACHE", "data/cache"))

SYSTEM = """You extract structured data from NASA microgravity combustion papers and reports
(PSI database: BASS, BASS-II, Saffire, FLEX, FLEX-2, CFI, ACME (BRE, CFI-G, E-FIELD, ...), SPICE, SLICE, SAME, SAME-R, DAFT).

Rules:
- One record per distinct test condition (fuel + atmosphere + flow). If a table lists many tests, group
  near-identical ones and keep the ones that differ in fuel, O2, pressure, flow or outcome. Max 25 records.
- Never invent numbers. If a value is not stated, leave it null.
- Convert units: pressure -> kPa (1 atm = 101.3 kPa, 1 psi = 6.895 kPa); O2 -> percent; flow -> cm/s; spread rate -> mm/s.
- gravity_g: ~0 for ISS/drop tower/parabolic microgravity, 1 for normal-gravity ground tests.
- quote must be copied verbatim from the text and support the key numbers. page = the [page N] marker it came from.
- confidence: 0.9 if all numbers are explicit in a table/text, 0.5 if partly inferred, 0.2 if guessy.
- Scope note: rocket/propellant combustion is out of scope; skip it."""

TOOL = {
    "name": "save_tests",
    "description": "Save every test condition found in the document.",
    "input_schema": ExtractionResult.model_json_schema(),
}


def _cache_path(pdf: Path) -> Path:
    h = hashlib.sha1(pdf.read_bytes()).hexdigest()[:12]
    return CACHE_DIR / f"{pdf.stem}.{h}.json"


def extract_from_text(text: str, meta: dict | None = None, client: anthropic.Anthropic | None = None) -> list[TestRecord]:
    client = client or anthropic.Anthropic()
    meta = meta or {}
    hint = "\n".join(f"{k}: {v}" for k, v in meta.items() if v)
    msg = client.messages.create(
        model=MODEL,
        max_tokens=12000,
        system=SYSTEM,
        tools=[TOOL],
        tool_choice={"type": "tool", "name": "save_tests"},
        messages=[{"role": "user", "content": f"Known metadata:\n{hint or '(none)'}\n\nDocument:\n{text}"}],
    )
    block = next(b for b in msg.content if b.type == "tool_use")
    result = ExtractionResult.model_validate(block.input)
    for t in result.tests:                          # metadata from sources.csv wins
        t.source_title = meta.get("title") or t.source_title
        t.source_url = meta.get("url") or t.source_url
        t.investigation = t.investigation or meta.get("investigation", "")
    return result.tests


MAX_WINDOWS = int(os.getenv("FLAMEATLAS_MAX_WINDOWS", "6"))


def build_windows(pdf: Path) -> list[str]:
    """Text windows to send to the LLM. Long reports (e.g. 144-page BASS-II summary)
    are reduced to the data-rich pages plus clean markdown tables."""
    pages = pdf_pages(pdf)
    if len(document_text(pages, 10**9)) < 500:
        raise ValueError(f"{pdf.name}: almost no text extracted (scanned PDF?)")
    tables_md: dict[int, str] = {}
    if len(pages) > 30:   # only worth it for long reports with test matrices
        for t in document_tables(pdf):
            if len(t["rows"]) >= 3:
                md = to_markdown(t["rows"])
                tables_md[t["page"]] = tables_md.get(t["page"], "") + md + "\n"
    return select_context(pages, tables_md)[:MAX_WINDOWS]


def _dedupe(tests: list[TestRecord]) -> list[TestRecord]:
    seen, out = set(), []
    for t in tests:
        key = (t.investigation, (t.fuel or "").lower(), t.o2_percent, t.pressure_kpa,
               t.flow_speed_cm_s, t.gravity_g, t.outcome)
        if key not in seen:
            seen.add(key)
            out.append(t)
    return out


def extract_from_pdf(pdf: str | Path, meta: dict | None = None, use_cache: bool = True) -> list[TestRecord]:
    pdf = Path(pdf)
    cache = _cache_path(pdf)
    if use_cache and cache.exists():
        return [TestRecord.model_validate(r) for r in json.loads(cache.read_text())]
    client = anthropic.Anthropic()
    tests: list[TestRecord] = []
    for window in build_windows(pdf):
        tests += extract_from_text(window, meta, client)
    tests = _dedupe(tests)
    CACHE_DIR.mkdir(parents=True, exist_ok=True)
    cache.write_text(json.dumps([t.model_dump(mode="json") for t in tests], ensure_ascii=False, indent=1))
    return tests
