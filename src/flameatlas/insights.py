"""The "interpret" part: Claude turns ranked tests + source passages into
fire-safety insights. Every claim must cite a test id [T0012] or a source [S3].
Nothing is stated that the provided data does not support."""
from __future__ import annotations

import json
import os

import anthropic
import pandas as pd
from dotenv import load_dotenv

from .retrieval import search

load_dotenv()
MODEL = os.getenv("FLAMEATLAS_MODEL", "claude-sonnet-5-5")

ROW_COLS = ["test_id", "investigation", "platform", "fuel", "phase", "sample_geometry", "pressure_kpa",
            "o2_percent", "diluent", "flow_speed_cm_s", "gravity_g", "outcome", "spread_rate_mm_s",
            "key_finding", "source_title", "page", "confidence", "relevance"]

GUARD = """You are FlameAtlas, a fire-safety analyst for crewed spacecraft, lunar/Martian bases and pressurized rovers.
Use ONLY the test records and source passages given. Cite every factual claim: test ids like [T0012], passages like [S3].
If the data does not answer something, say so plainly — never fill gaps from general knowledge without labeling it
"(general knowledge, not from PSI data)". Keep units. Be concise and concrete; the audience is aerospace engineers and students.
Context: the PSI database has no partial-gravity combustion data; microgravity and 1 g results bound lunar (0.16 g)
and Martian (0.38 g) behavior. Rocket/propellant combustion is out of scope."""


def _client() -> anthropic.Anthropic:
    return anthropic.Anthropic(timeout=300, max_retries=3)


def _text(msg) -> str:
    return "".join(b.text for b in msg.content if getattr(b, "type", "") == "text").strip()


def _rows(df: pd.DataFrame, n: int = 12) -> str:
    cols = [c for c in ROW_COLS if c in df.columns]
    recs = df[cols].head(n).to_dict(orient="records")
    recs = [{k: v for k, v in r.items() if pd.notna(v) and v != ""} for r in recs]
    return json.dumps(recs, ensure_ascii=False, default=str)


def _passages(hits: list[dict]) -> tuple[str, list[dict]]:
    text = "\n\n".join(f"[S{i}] ({h['investigation']}, {h['title']}, p.{h['page']})\n{h['text']}"
                       for i, h in enumerate(hits, start=1))
    refs = [{"id": f"S{i}", "title": h["title"], "url": h["url"], "page": h["page"]}
            for i, h in enumerate(hits, start=1)]
    return text, refs


def mission_insight(top: pd.DataFrame, mission: str, target: dict, client=None) -> dict:
    """Insight card for the selected crew environment.
    Returns {"markdown": str, "sources": [...]} ."""
    client = client or _client()
    q = (f"flammability spread extinction oxygen {target.get('o2_percent')} percent pressure "
         f"{target.get('pressure_kpa')} kPa flow {target.get('flow_speed_cm_s')} cm/s {target.get('phase') or ''}")
    passages, refs = _passages(search(q, k=6))
    prompt = f"""Crew environment: {mission}
Target conditions: {json.dumps(target)}

Most relevant tests (ranked by similarity of conditions):
{_rows(top)}

Source passages:
{passages or '(none)'}

Write the insight card in markdown with exactly these sections:
**Risk level:** Low / Moderate / High / Unknown — one sentence why, with citations.
**What the experiments show** — 3 bullets max.
**Gaps & bounds** — what is missing (e.g. partial gravity, untested O2/pressure) and how 0 g / 1 g data bound it.
**Design implications** — 2 bullets for material selection, airflow, detection or suppression."""
    msg = client.messages.create(model=MODEL, max_tokens=1200, system=GUARD,
                                 messages=[{"role": "user", "content": prompt}])
    return {"markdown": _text(msg), "sources": refs}


def ask(question: str, df: pd.DataFrame | None = None, history: list[dict] | None = None, client=None) -> dict:
    """Q&A over the corpus. history = previous [{"role","content"}] turns (optional)."""
    client = client or _client()
    passages, refs = _passages(search(question, k=8))
    rows = ""
    if df is not None and len(df):
        words = [w for w in question.lower().split() if len(w) > 3]
        text = df.fillna("").astype(str).agg(" ".join, axis=1).str.lower()
        mask = text.apply(lambda s: any(w in s for w in words))
        rows = _rows(df[mask] if mask.any() else df, n=15)
    user = f"""Question: {question}

Test records:
{rows or '(none)'}

Source passages:
{passages or '(none)'}

Answer in 3-8 sentences or a short list, with citations."""
    msgs = (history or [])[-6:] + [{"role": "user", "content": user}]
    msg = client.messages.create(model=MODEL, max_tokens=900, system=GUARD, messages=msgs)
    return {"markdown": _text(msg), "sources": refs}


def compare_investigations(df: pd.DataFrame, a: str, b: str, client=None) -> dict:
    """'How are investigations A and B similar / different?' — a challenge hint."""
    client = client or _client()
    sub = df[df["investigation"].isin([a, b])]
    passages, refs = _passages(search(f"{a} {b} objective fuel hardware results", k=6))
    prompt = f"""Compare {a} and {b}: objectives, fuels and sample geometry, test conditions (O2, pressure, flow),
hardware, measurements, and what each contributes to fire safety. Use a markdown table, then 2-3 bullets of takeaways.

Test records:
{_rows(sub, n=30)}

Source passages:
{passages or '(none)'}"""
    msg = client.messages.create(model=MODEL, max_tokens=1400, system=GUARD,
                                 messages=[{"role": "user", "content": prompt}])
    return {"markdown": _text(msg), "sources": refs}
