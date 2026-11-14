"""Streamlit blocks for the AI features: insight, Q&A, compare, investigations."""
from __future__ import annotations

import json
import os
from io import StringIO

import pandas as pd
import streamlit as st

from . import insights


def _has_key() -> bool:
    if os.getenv("ANTHROPIC_API_KEY"):
        return True
    try:
        if "ANTHROPIC_API_KEY" in st.secrets:
            os.environ["ANTHROPIC_API_KEY"] = st.secrets["ANTHROPIC_API_KEY"]
            return True
    except Exception:
        pass
    return False


def _cited_tests(markdown: str, df: pd.DataFrame | None):
    """Table of the test records the answer cites ([T0012] ...) — click-through traceability."""
    import re
    if df is None or "test_id" not in df:
        return
    ids = list(dict.fromkeys(re.findall(r"T\d{4}", markdown)))
    sub = df[df["test_id"].isin(ids)]
    if sub.empty:
        return
    cols = [c for c in ["test_id", "investigation", "fuel", "o2_percent", "pressure_kpa", "flow_speed_cm_s",
                        "gravity_g", "outcome", "key_finding", "quote", "page", "psi_url", "source_url"] if c in sub]
    with st.expander(f"Cited tests ({len(sub)})"):
        cfg = {}
        if "psi_url" in cols:
            cfg["psi_url"] = st.column_config.LinkColumn("PSI", display_text="open")
        if "source_url" in cols:
            cfg["source_url"] = st.column_config.LinkColumn("Paper", display_text="open")
        st.dataframe(sub[cols], hide_index=True, column_config=cfg)


def _sources(refs: list[dict]):
    if not refs:
        return
    with st.expander("Sources"):
        for r in refs:
            link = f"[{r['title']}]({r['url']})" if r.get("url") else r["title"]
            st.markdown(f"**{r['id']}** · {link}, p. {r['page']}")


@st.cache_data(show_spinner=False, ttl=3600)
def _cached_insight(top_json: str, mission: str, target_json: str) -> dict:
    return insights.mission_insight(pd.read_json(StringIO(top_json)), mission, json.loads(target_json))


def render_insight(top: pd.DataFrame, mission: str, target: dict, df: pd.DataFrame | None = None):
    st.subheader("AI insight")
    if not _has_key():
        st.info("Add ANTHROPIC_API_KEY to .env to enable AI insights.")
        return
    key = f"insight::{mission}::{json.dumps(target, sort_keys=True)}"
    if st.button("Generate insight for these conditions", type="primary"):
        with st.spinner("Reading the experiments..."):
            try:
                st.session_state[key] = _cached_insight(top.to_json(), mission, json.dumps(target, sort_keys=True))
            except Exception as e:
                st.error(f"AI call failed: {e}")
    if key in st.session_state:
        res = st.session_state[key]
        st.markdown(res["markdown"])
        _cited_tests(res["markdown"], df if df is not None else top)
        _sources(res["sources"])


def render_chat(df: pd.DataFrame):
    st.subheader("Ask the experiments")
    if not _has_key():
        st.info("Add ANTHROPIC_API_KEY to .env to enable Q&A.")
        return
    hist = st.session_state.setdefault("chat", [])
    for m in hist:
        with st.chat_message(m["role"]):
            st.markdown(m["content"])
    examples = ["Which materials kept burning at the lowest airflow?",
                "Does helium or CO2 suppress droplet flames better?",
                "What does Saffire tell us about large fires in spacecraft?"]
    pick = st.pills("Try:", examples, selection_mode="single") if hasattr(st, "pills") else None
    q = st.chat_input("Ask about microgravity fire safety...") or pick
    if q and (not hist or hist[-1]["content"] != q):
        hist.append({"role": "user", "content": q})
        with st.chat_message("user"):
            st.markdown(q)
        with st.chat_message("assistant"):
            with st.spinner("Searching the PSI documents..."):
                try:
                    res = insights.ask(q, df, history=hist[:-1])
                    st.markdown(res["markdown"])
                    _cited_tests(res["markdown"], df)
                    _sources(res["sources"])
                    hist.append({"role": "assistant", "content": res["markdown"]})
                except Exception as e:
                    st.error(f"AI call failed: {e}")


def render_compare(df: pd.DataFrame):
    st.subheader("Compare investigations")
    invs = sorted(df["investigation"].dropna().unique())
    if len(invs) < 2:
        st.caption("Need at least two investigations in the data.")
        return
    c1, c2 = st.columns(2)
    a = c1.selectbox("Investigation A", invs, index=0)
    b = c2.selectbox("Investigation B", invs, index=1)
    if st.button("Compare") and _has_key():
        with st.spinner("Comparing..."):
            try:
                res = insights.compare_investigations(df, a, b)
                st.markdown(res["markdown"])
                _cited_tests(res["markdown"], df)
                _sources(res["sources"])
            except Exception as e:
                st.error(f"AI call failed: {e}")


def render_investigations(df: pd.DataFrame):
    """Catalog of PSI combustion investigations ranked by fire-safety relevance."""
    from .catalog import load_catalog
    cat = load_catalog()
    if cat.empty:
        st.caption("data/psi_catalog.csv not found.")
        return
    counts = df["investigation"].value_counts() if "investigation" in df else pd.Series(dtype=int)
    view = cat.assign(tests_extracted=cat["acronym"].map(counts).fillna(0).astype(int))
    tier_name = {1: "Core fire safety", 2: "Related combustion", 3: "Indirect / modeling"}
    view["relevance"] = view["relevance_tier"].map(tier_name)
    cats = st.multiselect("Category", sorted(view["category"].unique()), default=[])
    if cats:
        view = view[view["category"].isin(cats)]
    st.dataframe(
        view[["psi_id", "acronym", "relevance", "category", "hardware", "tests_extracted", "objectives", "url"]],
        hide_index=True,
        column_config={"url": st.column_config.LinkColumn("PSI page (cite)", display_text="open"),
                       "objectives": st.column_config.TextColumn(width="large")},
    )
    st.caption("Data: NASA Physical Sciences Informatics (PSI). Cite each investigation via its DOI on the PSI page.")
