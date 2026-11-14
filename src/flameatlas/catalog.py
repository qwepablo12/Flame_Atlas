"""PSI investigation catalog + canonical investigation names."""
from __future__ import annotations

import re
from pathlib import Path

import pandas as pd

CATALOG = Path("data/psi_catalog.csv")

KNOWN = {
    "BASS":          ("prevention",  "MSG (SPICE flow duct)", 1),
    "BASS-II":       ("prevention",  "MSG (SPICE flow duct)", 1),
    "SAFFIRE-I":     ("prevention",  "Cygnus",                1),
    "SAFFIRE-II":    ("prevention",  "Cygnus",                1),
    "SAFFIRE-III":   ("prevention",  "Cygnus",                1),
    "SAME":          ("detection",   "MSG",                   1),
    "SAME-R":        ("detection",   "MSG",                   1),
    "FLEX":          ("suppression", "CIR/MDCA",              1),
    "FLEX-2":        ("suppression", "CIR/MDCA",              1),
    "ACME BRE":      ("prevention",  "CIR/ACME",              1),
    "CFI":           ("fundamental", "CIR/MDCA",              2),
    "ACME CFI-G":    ("fundamental", "CIR/ACME",              2),
    "SPICE":         ("fundamental", "MSG (SPICE flow duct)", 2),
    "SLICE":         ("fundamental", "MSG (SPICE flow duct)", 2),
    "ACME/Flame Design": ("fundamental", "CIR/ACME",          2),
    "ACME CLD Flame":    ("fundamental", "CIR/ACME",          2),
    "ACME E-FIELD Flames": ("fundamental", "CIR/ACME",        2),
    "ACME s-Flame":  ("fundamental", "CIR/ACME",              2),
    "DAFT":          ("detection",   "ISS cabin",             2),
    "STDCE-1":       ("fundamental", "Space Shuttle",         3),
}

ALIASES = {
    r"^saffire[-\s]?(1|i)$": "SAFFIRE-I", r"^saffire[-\s]?(2|ii)$": "SAFFIRE-II",
    r"^saffire[-\s]?(3|iii)$": "SAFFIRE-III", r"^saffire[-\s]?(6|vi)$": "SAFFIRE-VI",
    r"^saffire[-\s]?(4|iv)\s*(/|and|&|-)?\s*(5|v)?$": "SAFFIRE-IV/V", r"^saffire[-\s]?(5|v)$": "SAFFIRE-IV/V",
    r"^bass[-\s]?(2|ii)$": "BASS-II", r"^bass$": "BASS",
    r"^flex[-\s]?2$": "FLEX-2", r"^flex$": "FLEX",
    r"^same[-\s]?(r|2|reflight)$": "SAME-R", r"^same$": "SAME",
    r"^acme.*bre|^bre$|burning rate emulator": "ACME BRE",
    r"^acme.*cfi[-\s]?g": "ACME CFI-G",
    r"^acme.*flame design": "ACME/Flame Design",
    r"^acme.*s[-\s]?flame|spherical diffusion": "ACME s-Flame",
    r"^acme.*e[-\s]?field": "ACME E-FIELD Flames",
    r"^acme.*(cld|coflow)": "ACME CLD Flame",
    r"^cfi$|cool flames investigation$": "CFI",
}


def canonical(name: str) -> str:
    n = (name or "").strip()
    low = n.lower()
    for pat, canon in ALIASES.items():
        if re.search(pat, low):
            return canon
    return n


def _acronym(title: str) -> str:
    m = re.search(r"\(([^()]*)\)\s*$", title)
    a = m.group(1) if m else ""
    a = a.replace("ACME/s-Flame", "ACME s-Flame")
    return canonical(a) if a else ""


def load_catalog() -> pd.DataFrame:
    if not CATALOG.exists():
        return pd.DataFrame()
    df = pd.read_csv(CATALOG).fillna("")
    df["acronym"] = df["title"].map(_acronym)
    df.loc[df["title"].str.contains("Dust and Aerosol", case=False), "acronym"] = "DAFT"
    info = df["acronym"].map(lambda a: KNOWN.get(a, ("modeling" if a == "" else "fundamental", "", 3)))
    df["category"] = [i[0] for i in info]
    df["hardware"] = [i[1] for i in info]
    df["relevance_tier"] = [i[2] for i in info]
    ground = df["type"].str.contains("Ground", case=False)
    df.loc[ground, "category"] = "modeling / analysis"
    df.loc[ground & (df["relevance_tier"] < 3), "relevance_tier"] = 3
    off_topic = df["title"].str.contains("Solder", case=False)
    df = df[~off_topic]
    return df.sort_values(["relevance_tier", "acronym"]).reset_index(drop=True)


def psi_link(acronym: str, catalog: pd.DataFrame | None = None) -> tuple[str, str]:
    """(PSI id, url) for an investigation acronym, or ('', '')."""
    cat = load_catalog() if catalog is None else catalog
    hit = cat[cat["acronym"] == canonical(acronym)]
    if hit.empty:
        return "", ""
    return hit.iloc[0]["psi_id"], hit.iloc[0]["url"]
