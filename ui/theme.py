import streamlit as st

FLAME = "#FF7A3D"
EMBER = "#FFB347"
BLUE = "#58A6FF"
MUTED = "#8B949E"

OUTCOME_COLORS = {
    "ignited_spread": "#FF5A36",
    "ignited_no_spread": "#FFB347",
    "no_ignition": "#58A6FF",
    "extinguished": "#7EE787",
    "detected": "#D2A8FF",
    "other": "#8B949E",
    "unknown": "#484F58",
}

OUTCOME_LABELS = {
    "ignited_spread": "Ignited & spread",
    "ignited_no_spread": "Ignited, no spread",
    "no_ignition": "No ignition",
    "extinguished": "Extinguished",
    "detected": "Detected (smoke)",
    "other": "Other",
    "unknown": "Unknown",
}

CSS = """
<style>
.block-container {padding-top: 2rem; max-width: 1400px;}
</style>
"""


def apply():
    st.markdown(CSS, unsafe_allow_html=True)
