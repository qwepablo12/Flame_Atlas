"""Generate data/processed/experiments_mock.csv so the dashboard can be built before real extraction is ready."""
from __future__ import annotations

import random
import sys
from pathlib import Path

import pandas as pd

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src"))
from flameatlas.schema import CSV_COLUMNS

random.seed(42)
ROOT = Path(__file__).resolve().parents[1]

TEMPLATES = [
    ("BASS-II", "MSG", "ISS", "prevention", "PMMA", "solid", "thin sheet"),
    ("BASS-II", "MSG", "ISS", "prevention", "cotton-fiberglass fabric", "solid", "sheet"),
    ("Saffire-II", "Cygnus", "Cygnus", "prevention", "Nomex", "solid", "large sheet"),
    ("FLEX-2", "CIR/MDCA", "ISS", "suppression", "n-heptane", "liquid", "droplet"),
    ("FLEX", "CIR/MDCA", "ISS", "suppression", "methanol", "liquid", "droplet"),
    ("ACME-BRE", "CIR/ACME", "ISS", "prevention", "ethylene", "gas", "porous burner"),
    ("ACME-CFI-G", "CIR/ACME", "ISS", "fundamental", "propane", "gas", "spherical burner"),
    ("SAME-R", "MSG", "ISS", "detection", "silicone rubber (smoke)", "aerosol", "heated sample"),
]


def main():
    rows = []
    for i in range(40):
        inv, hw, plat, cat, fuel, phase, geom = random.choice(TEMPLATES)
        o2 = random.choice([16, 18, 21, 25, 30, 34, 40])
        flow = random.choice([0, 2, 5, 10, 20]) if phase != "liquid" else 0
        g = 1.0 if random.random() < 0.2 else 0.0
        spread = round(max(0, (o2 - 16) * 0.08 + flow * 0.02 + random.uniform(-0.2, 0.2)), 2) if phase == "solid" else None
        outcome = "ignited_spread" if (o2 >= 21 or flow > 0) else random.choice(["no_ignition", "extinguished"])
        if cat == "detection":
            outcome, spread = "detected", None
        rows.append({
            "investigation": inv, "hardware": hw, "platform": plat, "year": random.choice([2012, 2016, 2019, 2022]),
            "category": cat, "objective": f"MOCK objective for {inv}", "fuel": fuel, "phase": phase,
            "sample_geometry": geom, "pressure_kpa": random.choice([101.3, 70.3, 55.0]), "o2_percent": o2,
            "diluent": "N2", "flow_speed_cm_s": flow, "gravity_g": g, "outcome": outcome,
            "spread_rate_mm_s": spread, "measurements": "color video, thermocouples",
            "key_finding": "MOCK finding — not real data", "quote": "MOCK", "source_title": "MOCK",
            "source_url": "", "page": None, "confidence": round(random.uniform(0.4, 0.95), 2),
        })
    df = pd.DataFrame(rows, columns=CSV_COLUMNS)
    df.insert(0, "test_id", [f"M{i:04d}" for i in range(1, len(df) + 1)])
    out = ROOT / "data/processed/experiments_mock.csv"
    out.parent.mkdir(parents=True, exist_ok=True)
    df.to_csv(out, index=False)
    print(f"{len(df)} mock rows -> {out}")


if __name__ == "__main__":
    main()
