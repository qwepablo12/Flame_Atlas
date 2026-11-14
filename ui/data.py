from pathlib import Path

import pandas as pd
import streamlit as st

from flameatlas.catalog import load_catalog

DATA = Path("data/processed")


@st.cache_data(show_spinner=False)
def load_tests() -> tuple[pd.DataFrame, bool]:
    real = DATA / "experiments.csv"
    path, is_real = (real, True) if real.exists() else (DATA / "experiments_mock.csv", False)
    df = pd.read_csv(path)
    cat = load_catalog()
    if not cat.empty:
        info = cat[cat["acronym"] != ""].drop_duplicates("acronym").set_index("acronym")
        df["category"] = df["investigation"].map(info["category"]).fillna(df["category"])
        df["relevance_tier"] = df["investigation"].map(info["relevance_tier"]).fillna(3).astype(int)
    else:
        df["relevance_tier"] = 3
    for col in ["fuel", "phase", "outcome", "investigation", "key_finding", "quote", "source_title"]:
        if col in df:
            df[col] = df[col].fillna("")
    return df, is_real


@st.cache_data(show_spinner=False)
def load_sources() -> pd.DataFrame:
    return pd.read_csv("data/sources.csv", dtype=str).fillna("")


def key_finding(df: pd.DataFrame) -> dict | None:
    hit = df[df["quote"].str.contains("steady spreading at 13.6% oxygen", case=False, regex=False)]
    return hit.iloc[0].to_dict() if len(hit) else None
