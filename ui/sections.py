import pandas as pd
import streamlit as st

from flameatlas.missions import MISSIONS, PSI_TO_KPA
from flameatlas.rank import gravity_bounds

from . import charts
from .theme import OUTCOME_LABELS

TABLE_COLS = ["relevance", "test_id", "investigation", "fuel", "phase", "o2_percent", "pressure_kpa",
              "flow_speed_cm_s", "gravity_g", "outcome"]


def hero(finding: dict | None):
    st.title("FlameAtlas")
    st.caption("NASA microgravity combustion experiments, ranked and summarized for fire safety in spacecraft, "
               "lunar and Martian habitats, and pressurized rovers.")
    if finding:
        with st.container(border=True):
            st.markdown(
                "**Key finding (BASS-II).** In microgravity, a PMMA rod sustained flame spread at 13.6% O₂, "
                "below its 16% blowoff limit in normal gravity. Flammability limits measured on Earth are not "
                "necessarily conservative for spacecraft.")
            st.caption(f'"{finding["quote"]}" {finding["source_title"]}, p. {int(finding["page"])}, '
                       f'test {finding["test_id"]}.')


def kpis(df: pd.DataFrame, sources: pd.DataFrame, n_psi: int):
    c = st.columns(4)
    c[0].metric("Test records", len(df))
    c[1].metric("Investigations", df["investigation"].nunique())
    c[2].metric("Source documents", len(sources))
    c[3].metric("PSI investigations cataloged", n_psi)


def how_to():
    with st.expander("How to use FlameAtlas"):
        st.markdown(
            "1. Choose a crew environment in the sidebar, or set O₂, pressure and airflow.\n"
            "2. Review the most similar tests, ranked by how close their conditions are.\n"
            "3. Generate an AI insight: risk level, evidence, data gaps and design implications. Each claim cites "
            "a test record such as [T0001] or a source page.\n"
            "4. Ask questions, compare investigations, and open any test to see the quote from the source document.")


def sidebar(df: pd.DataFrame) -> tuple[str, dict, pd.DataFrame]:
    with st.sidebar:
        st.markdown("### Crew environment")
        preset = st.selectbox("Preset", list(MISSIONS), label_visibility="collapsed")
        m = MISSIONS[preset]
        o2 = st.slider("O₂ (%)", 10.0, 100.0, float(m["o2_percent"]), 0.5)
        p = st.slider("Pressure (kPa)", 20.0, 110.0, float(m["pressure_kpa"]), 0.5,
                      help="1 psi = 6.895 kPa")
        st.caption(f"= {p / PSI_TO_KPA:.1f} psi")
        flow = st.slider("Airflow (cm/s)", 0.0, 40.0, 5.0, 0.5,
                         help="Cabin ventilation / imposed flow. 0 = still air.")
        phase = st.selectbox("Fuel phase", ["any", "solid", "liquid", "gas"])
        st.markdown("### Filters")
        invs = st.multiselect("Investigations", sorted(df["investigation"].unique()))
        cats = st.multiselect("Fire-safety category", sorted(df["category"].dropna().unique()))
        core = st.toggle("Core fire-safety investigations only", value=False,
                         help="BASS, BASS-II, Saffire, SAME, SAME-R, FLEX, FLEX-2, ACME BRE")
    f = df
    if invs:
        f = f[f["investigation"].isin(invs)]
    if cats:
        f = f[f["category"].isin(cats)]
    if core:
        f = f[f["relevance_tier"] == 1]
    target = {"o2_percent": o2, "pressure_kpa": p, "flow_speed_cm_s": flow,
              "gravity_g": m["gravity_g"], "phase": None if phase == "any" else phase}
    return preset, target, f


def environment_card(preset: str, target: dict):
    m = MISSIONS[preset]
    c = st.columns([1, 1, 1, 2])
    d_o2 = target["o2_percent"] - 21
    c[0].metric("Oxygen", f"{target['o2_percent']:.1f}%",
                f"{d_o2:+.1f} pts vs air" if abs(d_o2) >= 0.5 else None, delta_color="inverse")
    c[1].metric("Pressure", f"{target['pressure_kpa']:.1f} kPa")
    c[1].caption(f"{target['pressure_kpa'] / PSI_TO_KPA:.1f} psi · Earth sea level 14.7 psi")
    c[2].metric("Gravity", f"{m['gravity_g']:g} g")
    with c[3]:
        st.markdown(f"**{preset}**")
        st.caption(m["note"])
        if 0 < m["gravity_g"] < 1:
            st.caption("PSI has no partial-gravity combustion data. See the Gravity bounds tab.")


def test_detail(row: pd.Series):
    st.caption(" · ".join(x for x in [row["investigation"], row.get("platform") if isinstance(row.get("platform"), str) else "",
                                       OUTCOME_LABELS.get(row["outcome"], row["outcome"])] if x))
    st.markdown(f"#### {row['test_id']} · {row['fuel'] or 'unspecified fuel'}")
    c = st.columns(5)
    fmt = lambda v, u: "—" if pd.isna(v) else f"{v:g} {u}"
    c[0].metric("O₂", fmt(row["o2_percent"], "%"))
    c[1].metric("Pressure", fmt(row["pressure_kpa"], "kPa"))
    c[2].metric("Airflow", fmt(row["flow_speed_cm_s"], "cm/s"))
    c[3].metric("Gravity", fmt(row["gravity_g"], "g"))
    c[4].metric("Confidence", fmt(row["confidence"], ""))
    if row["key_finding"]:
        st.markdown(f"**Finding:** {row['key_finding']}")
    if row["quote"]:
        st.markdown(f'> "{row["quote"]}"')
    page = "" if pd.isna(row.get("page")) else f", p. {int(row['page'])}"
    links = []
    if isinstance(row.get("source_url"), str) and row["source_url"]:
        links.append(f"[Source document]({row['source_url']})")
    if isinstance(row.get("psi_url"), str) and row["psi_url"]:
        links.append(f"[PSI {row.get('psi_id', '')}]({row['psi_url']})")
    st.caption(f"{row['source_title']}{page}  ·  " + "  ·  ".join(links))


def explore(df: pd.DataFrame, top: pd.DataFrame, target: dict):
    left, right = st.columns([5, 4])
    with left:
        st.markdown("#### Most relevant tests")
        st.caption("Ranked by similarity of O₂, pressure, airflow and gravity to your environment.")
        if top.empty:
            st.info("No tests match the current filters.")
        else:
            st.dataframe(
                top[[c for c in TABLE_COLS if c in top]], hide_index=True, height=390,
                column_config={
                    "relevance": st.column_config.ProgressColumn("Match", min_value=0, max_value=1, format="%.2f"),
                    "test_id": "Test", "investigation": "Investigation", "fuel": "Fuel / material",
                    "phase": "Phase", "o2_percent": st.column_config.NumberColumn("O₂ %", format="%.1f"),
                    "pressure_kpa": st.column_config.NumberColumn("kPa", format="%.1f"),
                    "flow_speed_cm_s": st.column_config.NumberColumn("Flow cm/s", format="%.1f"),
                    "gravity_g": st.column_config.NumberColumn("g", format="%g"),
                    "outcome": "Outcome",
                })
    with right:
        fig = charts.flammability_map(df, target)
        if fig:
            st.plotly_chart(fig, width="stretch")
        else:
            st.info("Not enough O₂ + airflow data for the map.")
    if not top.empty:
        st.markdown("#### Test details")
        choice = st.selectbox("Open a test", top["test_id"] + " · " + top["investigation"] + " · " + top["fuel"],
                              label_visibility="collapsed")
        test_detail(top[top["test_id"] == choice.split(" · ")[0]].iloc[0])
    c1, c2 = st.columns(2)
    with c1:
        fig = charts.o2_by_investigation(df, target["o2_percent"])
        if fig:
            st.plotly_chart(fig, width="stretch")
    with c2:
        fig = charts.outcome_mix(df)
        if fig:
            st.plotly_chart(fig, width="stretch")


def gravity(df: pd.DataFrame, target: dict, preset: str):
    st.markdown("#### Bounding partial gravity with 0 g and 1 g data")
    st.markdown(
        "PSI currently has no partial-gravity combustion data. LUCI and FM2 are expected to add it later. "
        "Following the challenge guidance, microgravity and normal-gravity results are used as bounds for the "
        "Moon (0.16 g) and Mars (0.38 g).")
    b = gravity_bounds(df, target)
    fig = charts.gravity_compare(b["microgravity"], b["normal_gravity"])
    if fig:
        st.plotly_chart(fig, width="stretch")
    c1, c2 = st.columns(2)
    cols = ["test_id", "investigation", "fuel", "o2_percent", "flow_speed_cm_s", "outcome", "relevance"]
    with c1:
        st.markdown("**Microgravity bound (0 g)**")
        st.dataframe(b["microgravity"][cols], hide_index=True)
    with c2:
        st.markdown("**Normal-gravity bound (1 g)**")
        if b["normal_gravity"].empty:
            st.caption("No 1 g tests in the current selection.")
        else:
            st.dataframe(b["normal_gravity"][cols], hide_index=True)
    n1 = int((df["gravity_g"] > 0.9).sum())
    st.caption(f"Only {n1} of {len(df)} extracted test records are normal-gravity comparisons; most documents "
               "report 1 g behavior in text rather than as separate tests. Ask the AI tab about 1 g vs microgravity "
               "for the narrative evidence.")


EARTH = [
    ("Fine-water-mist extinguishers",
     "Developed for use on the ISS, fine-water-mist extinguishers have practical applications on Earth."),
    ("Smoke detection",
     "A smoke detector developed for the Space Shuttle in the 1970s distinguishes smoke from dust, which reduces "
     "nuisance alarms and is useful in industrial settings such as mining. SAME and SAME-R measured smoke particle "
     "sizes in microgravity to inform spacecraft detectors."),
    ("Firefighter air tanks",
     "In the 1970s, spacesuit technology was adapted to improve firefighters' air tanks and breathing gear."),
    ("Protective clothing",
     "In the 1980s, NASA spacesuit technology was applied to improve firefighter protective clothing."),
]


def on_earth():
    st.markdown("#### Applications on Earth")
    st.caption("Examples from the Flame in Freefall challenge resources.")
    cols = st.columns(2)
    for i, (title, text) in enumerate(EARTH):
        with cols[i % 2]:
            with st.container(border=True):
                st.markdown(f"**{title}**")
                st.markdown(text)
    st.markdown(
        "Microgravity data are also useful on Earth. Without buoyancy there are no rising hot gases, so flames "
        "rely on diffusion for their oxygen, and a candle flame becomes a dim blue sphere. Removing buoyancy lets "
        "researchers study combustion processes that are hidden by convection on Earth.")


def about(sources: pd.DataFrame):
    st.markdown("#### How FlameAtlas works")
    st.markdown(
        "1. **Collect** NASA reports and papers for the PSI combustion investigations (NTRS, PSI).\n"
        "2. **Extract** test conditions and outcomes with an LLM; every record keeps a verbatim quote and page "
        "number, and is validated in code. Long reports are reduced to their data-rich pages and test-matrix tables.\n"
        "3. **Rank** tests by similarity to a crew environment (O₂, pressure, airflow, gravity).\n"
        "4. **Interpret** with an LLM that may only use the retrieved records and passages and must cite each claim.")
    st.markdown("#### Sources")
    st.dataframe(sources[["investigation", "title", "doc_type", "year", "url"]], hide_index=True,
                 column_config={"url": st.column_config.LinkColumn("Link", display_text="open"),
                                "title": st.column_config.TextColumn(width="large")})


def footer():
    st.divider()
    st.caption("Data: NASA Physical Sciences Informatics (PSI) and NASA Technical Reports Server. Cite each "
               "investigation by the DOI on its PSI page. NASA Space Apps Challenge 2026, Flame in Freefall. "
               "AI use is disclosed in the project README.")
