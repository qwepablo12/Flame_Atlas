# FlameAtlas 

AI-powered dashboard that summarizes, ranks and interprets NASA microgravity combustion
experiments (PSI database) to deliver fire safety insights for crewed spacecraft, Moon bases
and pressurized rovers. NASA Space Apps Challenge 2026 — *Flame in Freefall*.

## Quick start

```bash
python -m venv .venv && source .venv/bin/activate   # Windows: .venv\Scripts\activate
pip install -r requirements.txt
cp .env.example .env                                 # add your ANTHROPIC_API_KEY
python scripts/make_mock_data.py                     # fake data for UI work
streamlit run app.py
```

## Pipeline (data/AI side)

1. Find documents for each investigation in `data/investigations.csv` (psi.nasa.gov, NTRS).
2. Add a row per document to `data/sources.csv`, put the PDF in `data/raw/`.
3. `python scripts/extract_all.py --limit 3` → check output → run on everything.
4. Output: `data/processed/experiments.csv` (one row = one test condition).

## Layout

```
app.py                      Streamlit dashboard (product side)
src/flameatlas/schema.py    Data contract — agree before changing
src/flameatlas/parse_pdf.py PDF → text/chunks
src/flameatlas/extract.py   LLM extraction → TestRecord rows (cached)
src/flameatlas/rank.py      Relevance to a crew environment + 0g/1g bounds
src/flameatlas/missions.py  ISS / Moon / Mars / spacesuit presets
data/investigations.csv     Target investigations from the challenge
data/sources.csv            Documents found (fill in)
```

## Team
- Data & AI — extraction pipeline, ranking, insights
- Product & Science — dashboard, physics review, pitch
