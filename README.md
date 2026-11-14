# FlameAtlas

An AI-powered dashboard that summarizes, ranks and interprets NASA microgravity combustion
experiments from the Physical Sciences Informatics (PSI) database to deliver fire safety insights
for spacecraft, space stations, lunar and Martian bases, and pressurized rovers.

NASA Space Apps Challenge 2026 — *Flame in Freefall: SI-Powered Fire Safety Insights from Microgravity Combustion Data*.

## What it does

- **Rank:** choose a crew environment (ISS cabin, Moon base / rover at ≥30% O₂ and ≤10.2 psi, Mars habitat, spacesuit)
  or set O₂, pressure and airflow, and see the most similar real test conditions from 174 extracted test records.
- **Interpret:** an AI insight card gives a risk level, what the experiments show, data gaps (no partial-gravity data
  in PSI, so 0 g and 1 g results are used as bounds) and design implications. Every claim cites a test record or a
  source page.
- **Ask:** questions answered only from the indexed NASA documents, with citations.
- **Compare:** side-by-side comparison of two investigations.
- **Investigations:** catalog of the PSI combustion investigations ranked by fire-safety relevance, linked to their
  PSI pages for citation.

## Run locally

```bash
python3.12 -m venv .venv && source .venv/bin/activate
pip install -r requirements.txt
cp .env.example .env        # add ANTHROPIC_API_KEY to enable the AI features
streamlit run app.py
```

## Data pipeline

```bash
python scripts/extract_all.py    # PDFs listed in data/sources.csv -> data/processed/experiments.csv
python scripts/build_index.py    # PDFs -> data/processed/chunks.jsonl (search index for Q&A)
```

PDFs go in `data/raw/` (not committed). Extraction results are cached per document in `data/cache/`.

## Layout

```
app.py                         Streamlit dashboard
src/flameatlas/schema.py       Test record schema
src/flameatlas/parse_pdf.py    PDF text, chunks, context selection for long reports
src/flameatlas/tables.py       Table extraction (incl. rotated test matrices)
src/flameatlas/extract.py      LLM extraction of test records, validation, caching
src/flameatlas/rank.py         Similarity ranking and 0 g / 1 g bounds
src/flameatlas/retrieval.py    BM25 search over document chunks
src/flameatlas/insights.py     Insight, Q&A and comparison prompts
src/flameatlas/catalog.py      PSI investigation catalog and name normalization
src/flameatlas/ui_ai.py        Streamlit blocks for the AI features
data/sources.csv               Source documents
data/psi_catalog.csv           PSI combustion investigations
data/processed/                Extracted test records and search index
```

## Data sources and citation

Test data come from NASA technical reports and papers (NASA Technical Reports Server) and the
[NASA Physical Sciences Informatics (PSI)](https://psi.nasa.gov) data repository. Each source is listed in
`data/sources.csv`. PSI asks users to cite each investigation by its DOI, available via
"Cite this Investigation" on its PSI page; the dashboard links every test record to its PSI investigation page.

## Use of AI

AI tools were used in two ways, disclosed here as required by the Space Apps rules.

**1. Inside the product (Claude API by Anthropic).**
- *Data extraction:* Claude reads NASA documents and extracts structured test records (fuel, O₂, pressure,
  airflow, gravity, outcome, key finding). Each record stores a verbatim quote and page number from the source so it
  can be checked, and records are validated in code.
- *Insights, Q&A and comparisons:* Claude writes answers using only the retrieved test records and document
  passages, and is instructed to cite every claim and to state when the data do not answer a question.
- Ranking of tests and the search index are deterministic code, not AI.

**2. During development (Claude as a coding assistant).**
Claude helped design the architecture and write and debug the Python code for the data pipeline (PDF parsing,
table extraction, LLM extraction, ranking, search) and the AI features. The team chose the challenge and approach,
collected the source documents, ran the pipeline, reviewed the extracted data against the sources and decided what
to build.

No AI-generated images, video or audio are used.

## Team

- Data & AI — sources, extraction pipeline, ranking, AI features
- Product & Frontend — dashboard design, charts, pitch
