"""FlameAtlas dashboard. Run: streamlit run app.py"""
import sys
from pathlib import Path

import pandas as pd
import plotly.express as px
import streamlit as st

sys.path.insert(0, str(Path(__file__).parent / "src"))
from flameatlas.missions import MISSIONS
from flameatlas.rank import rank
from flameatlas.ui_ai import render_chat, render_compare, render_insight, render_investigations

DATA = Path("data/processed")
real, mock = DATA / "experiments.csv", DATA / "experiments_mock.csv"

st.set_page_config(page_title="FlameAtlas", page_icon="🔥", layout="wide")
st.title("FlameAtlas")
st.caption("Fire safety insights from NASA microgravity combustion experiments")

if real.exists():
    df = pd.read_csv(real)
else:
    df = pd.read_csv(mock)
    st.warning("Showing MOCK data — real extraction not loaded yet.")

with st.sidebar:
    st.header("Crew environment")
    preset = st.selectbox("Preset", list(MISSIONS))
    m = MISSIONS[preset]
    o2 = st.slider("O2 (%)", 10.0, 100.0, float(m["o2_percent"]))
    p = st.slider("Pressure (kPa)", 20.0, 110.0, float(m["pressure_kpa"]))
    flow = st.slider("Airflow (cm/s)", 0.0, 30.0, 5.0)
    phase = st.selectbox("Fuel phase", ["any", "solid", "liquid", "gas", "aerosol"])
    st.caption(m["note"])

target = {"o2_percent": o2, "pressure_kpa": p, "flow_speed_cm_s": flow, "gravity_g": m["gravity_g"],
          "phase": None if phase == "any" else phase}
top = rank(df, target, top=10)

c1, c2 = st.columns([3, 2])
with c1:
    st.subheader("Most relevant tests")
    st.dataframe(top[["relevance", "investigation", "fuel", "o2_percent", "pressure_kpa",
                      "flow_speed_cm_s", "gravity_g", "outcome", "source_title"]], hide_index=True)
with c2:
    st.subheader("Spread rate vs O2")
    solid = df.dropna(subset=["spread_rate_mm_s"])
    fig = px.scatter(solid, x="o2_percent", y="spread_rate_mm_s", color="investigation",
                     hover_data=["fuel", "flow_speed_cm_s"])
    fig.add_vline(x=o2, line_dash="dash")
    st.plotly_chart(fig, width="stretch")

st.divider()
tab1, tab2, tab3, tab4 = st.tabs(["AI insight", "Ask", "Compare", "Investigations"])
with tab1:
    render_insight(top, preset, target, df)
with tab2:
    render_chat(df)
with tab3:
    render_compare(df)
with tab4:
    render_investigations(df)
