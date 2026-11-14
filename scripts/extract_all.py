"""Run extraction over every PDF listed in data/sources.csv that has a local_file.

Usage:
    python scripts/extract_all.py            # all sources with a downloaded PDF
    python scripts/extract_all.py --limit 3  # quick test
Output: data/processed/experiments.csv
"""
from __future__ import annotations

import argparse
import sys
from pathlib import Path

import pandas as pd

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src"))
from flameatlas.extract import extract_from_pdf  # noqa: E402
from flameatlas.catalog import canonical, load_catalog  # noqa: E402
from flameatlas.schema import CSV_COLUMNS  # noqa: E402

ROOT = Path(__file__).resolve().parents[1]


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--limit", type=int, default=None)
    ap.add_argument("--no-cache", action="store_true")
    args = ap.parse_args()

    src = pd.read_csv(ROOT / "data/sources.csv").fillna("")
    src = src[src["local_file"] != ""]
    # smallest documents first: quick feedback on the first runs
    src = src.assign(_size=src["local_file"].map(lambda f: (ROOT / "data/raw" / f).stat().st_size
                                                 if (ROOT / "data/raw" / f).exists() else 0))
    src = src.sort_values("_size")
    if args.limit:
        src = src.head(args.limit)

    rows, failed = [], []
    for _, s in src.iterrows():
        pdf = ROOT / "data/raw" / s["local_file"]
        if not pdf.exists():
            failed.append((s["local_file"], "file not found"))
            continue
        meta = {"investigation": s["investigation"], "title": s["title"], "url": s["url"]}
        try:
            tests = extract_from_pdf(pdf, meta, use_cache=not args.no_cache)
            rows += [t.model_dump(mode="json") for t in tests]
            print(f"OK   {s['local_file']}: {len(tests)} tests")
        except Exception as e:  # keep going, report at the end
            failed.append((s["local_file"], str(e)[:120]))
            print(f"FAIL {s['local_file']}: {e}")

    out = ROOT / "data/processed/experiments.csv"
    out.parent.mkdir(parents=True, exist_ok=True)
    df = pd.DataFrame(rows, columns=CSV_COLUMNS)
    df["investigation"] = df["investigation"].map(canonical)
    cat = load_catalog()
    if not cat.empty:   # link every test to its PSI dataset (PSI asks users to cite it)
        links = cat.set_index("acronym")[["psi_id", "url"]]
        df["psi_id"] = df["investigation"].map(links["psi_id"]).fillna("")
        df["psi_url"] = df["investigation"].map(links["url"]).fillna("")
    df.insert(0, "test_id", [f"T{i:04d}" for i in range(1, len(df) + 1)])
    df.to_csv(out, index=False)
    print(f"\n{len(df)} tests from {len(src) - len(failed)} documents -> {out}")
    for f, why in failed:
        print(f"  failed: {f} ({why})")


if __name__ == "__main__":
    main()
