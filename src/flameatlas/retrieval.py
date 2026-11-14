"""Lightweight search over document chunks (BM25, pure Python — no vector DB to install)."""
from __future__ import annotations

import json
import math
import re
from collections import Counter
from functools import lru_cache
from pathlib import Path

CHUNKS = Path("data/processed/chunks.jsonl")
TOKEN = re.compile(r"[a-z0-9]+(?:[.-][a-z0-9]+)*")
STOP = set("the a an of and or to in on for with by is are was were be been at as from that this it its "
           "these those which we our into than then there their can not no".split())


def tokenize(text: str) -> list[str]:
    return [t for t in TOKEN.findall(text.lower()) if t not in STOP and len(t) > 1]


class BM25:
    def __init__(self, docs: list[str], k1: float = 1.5, b: float = 0.75):
        self.toks = [tokenize(d) for d in docs]
        self.k1, self.b = k1, b
        self.avg = sum(map(len, self.toks)) / max(len(self.toks), 1)
        df = Counter(t for doc in self.toks for t in set(doc))
        n = len(self.toks)
        self.idf = {t: math.log(1 + (n - f + 0.5) / (f + 0.5)) for t, f in df.items()}
        self.tf = [Counter(doc) for doc in self.toks]

    def scores(self, query: str) -> list[float]:
        q = tokenize(query)
        out = []
        for tf, doc in zip(self.tf, self.toks):
            s = 0.0
            for t in q:
                if t in tf:
                    f = tf[t]
                    s += self.idf[t] * f * (self.k1 + 1) / (f + self.k1 * (1 - self.b + self.b * len(doc) / self.avg))
            out.append(s)
        return out


@lru_cache(maxsize=1)
def _index(path: str = str(CHUNKS)):
    chunks = [json.loads(line) for line in Path(path).read_text(encoding="utf-8").split("\n") if line.strip()]
    return chunks, BM25([c["text"] for c in chunks])


def search(query: str, k: int = 8, investigation: str | None = None) -> list[dict]:
    if not CHUNKS.exists():
        return []
    chunks, bm = _index()
    scored = sorted(zip(bm.scores(query), chunks), key=lambda x: -x[0])
    hits = []
    for s, c in scored:
        if s <= 0:
            break
        if investigation and investigation.lower() not in c.get("investigation", "").lower():
            continue
        hits.append({**c, "score": round(s, 2)})
        if len(hits) == k:
            break
    return hits
