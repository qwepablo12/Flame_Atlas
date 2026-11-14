"""FlameAtlas dashboard. Run: streamlit run app.py"""
import sys
from pathlib import Path

import streamlit as st

ROOT = Path(__file__).parent
sys.path.insert(0, str(ROOT / "src"))
sys.path.insert(0, str(ROOT))

from flameatlas.catalog import load_catalog
from flameatlas.rank import rank
from flameatlas.ui_ai import render_chat, render_compare, render_insight, render_investigations
from ui import sections, theme
from ui.data import key_finding, load_sources, load_tests

st.set_page_config(page_title="FlameAtlas", layout="wide")
theme.apply()

df_all, is_real = load_tests()
sources = load_sources()

sections.hero(key_finding(df_all))
if not is_real:
    st.warning("Showing mock data. Real extraction results are not loaded.")
sections.kpis(df_all, sources, len(load_catalog()))
sections.how_to()

preset, target, df = sections.sidebar(df_all)
st.divider()
sections.environment_card(preset, target)
top = rank(df, target, top=12) if len(df) else df

tabs = st.tabs(["Explore", "AI insight", "Ask", "Compare", "Investigations",
                "Gravity bounds", "On Earth", "About"])
with tabs[0]:
    sections.explore(df, top, target)
with tabs[1]:
    render_insight(top, preset, target, df_all)
with tabs[2]:
    render_chat(df_all)
with tabs[3]:
    render_compare(df_all)
with tabs[4]:
    render_investigations(df_all)
with tabs[5]:
    sections.gravity(df, target, preset)
with tabs[6]:
    sections.on_earth()
with tabs[7]:
    sections.about(sources)
sections.footer()
