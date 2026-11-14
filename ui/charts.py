import pandas as pd
import plotly.express as px
import plotly.graph_objects as go

from .theme import BLUE, FLAME, MUTED, OUTCOME_COLORS, OUTCOME_LABELS

LAYOUT = dict(
    paper_bgcolor="rgba(0,0,0,0)", plot_bgcolor="rgba(0,0,0,0)",
    font=dict(color="#C9D1D9", size=12), margin=dict(l=10, r=10, t=40, b=10),
    legend=dict(bgcolor="rgba(0,0,0,0)", font=dict(size=11)),
    xaxis=dict(gridcolor="#21262D", zerolinecolor="#30363D"),
    yaxis=dict(gridcolor="#21262D", zerolinecolor="#30363D"),
)


def _labelled(df: pd.DataFrame) -> pd.DataFrame:
    out = df.copy()
    out["Outcome"] = out["outcome"].map(OUTCOME_LABELS).fillna("Unknown")
    return out


def flammability_map(df: pd.DataFrame, target: dict) -> go.Figure | None:
    d = _labelled(df.dropna(subset=["o2_percent", "flow_speed_cm_s"]))
    if d.empty:
        return None
    fig = px.scatter(
        d, x="flow_speed_cm_s", y="o2_percent", color="Outcome",
        color_discrete_map={OUTCOME_LABELS[k]: v for k, v in OUTCOME_COLORS.items()},
        hover_data={"test_id": True, "fuel": True, "pressure_kpa": True, "investigation": True,
                    "flow_speed_cm_s": ":.1f", "o2_percent": ":.1f"},
        labels={"flow_speed_cm_s": "Airflow (cm/s)", "o2_percent": "O₂ (%)"},
    )
    fig.update_traces(marker=dict(size=9, line=dict(width=0.5, color="#0D1117")))
    fig.add_trace(go.Scatter(
        x=[target["flow_speed_cm_s"]], y=[target["o2_percent"]], mode="markers+text",
        marker=dict(symbol="x", size=16, color="white", line=dict(width=2, color=FLAME)),
        text=["your environment"], textposition="top center", textfont=dict(color=FLAME),
        name="Selected environment", showlegend=True))
    fig.add_hline(y=21, line_dash="dot", line_color=MUTED, annotation_text="air 21%",
                  annotation_position="bottom right", annotation_font_color=MUTED)
    fig.update_layout(**LAYOUT, title="Flammability map: oxygen vs airflow", height=430)
    fig.update_layout(legend=dict(orientation="h", yanchor="top", y=-0.18, x=0, title_text=""))
    fig.update_xaxes(type="log" if d["flow_speed_cm_s"].max() > 50 else "linear")
    return fig


def o2_by_investigation(df: pd.DataFrame, target_o2: float) -> go.Figure | None:
    d = _labelled(df.dropna(subset=["o2_percent"]))
    if d.empty:
        return None
    order = d.groupby("investigation")["o2_percent"].median().sort_values().index.tolist()
    fig = px.strip(
        d, x="o2_percent", y="investigation", color="Outcome",
        color_discrete_map={OUTCOME_LABELS[k]: v for k, v in OUTCOME_COLORS.items()},
        category_orders={"investigation": order}, hover_data=["test_id", "fuel"],
        labels={"o2_percent": "O₂ (%)", "investigation": ""},
    )
    fig.add_vline(x=target_o2, line_dash="dash", line_color=FLAME,
                  annotation_text=f"selected {target_o2:.0f}%", annotation_font_color=FLAME)
    fig.update_layout(**LAYOUT, title="Oxygen levels tested per investigation",
                      height=max(320, 34 * len(order) + 120))
    return fig


def outcome_mix(df: pd.DataFrame) -> go.Figure | None:
    d = _labelled(df)
    if d.empty:
        return None
    g = d.groupby(["investigation", "Outcome"]).size().reset_index(name="tests")
    order = d["investigation"].value_counts().index.tolist()[::-1]
    fig = px.bar(g, x="tests", y="investigation", color="Outcome", orientation="h",
                 category_orders={"investigation": order},
                 color_discrete_map={OUTCOME_LABELS[k]: v for k, v in OUTCOME_COLORS.items()},
                 labels={"tests": "Test records", "investigation": ""})
    fig.update_layout(**LAYOUT, title="Outcomes by investigation", height=max(320, 30 * len(order) + 120),
                      barmode="stack")
    return fig


def gravity_compare(micro: pd.DataFrame, earth: pd.DataFrame) -> go.Figure | None:
    rows = []
    for label, d in [("Microgravity (0 g)", micro), ("Normal gravity (1 g)", earth)]:
        for _, r in d.iterrows():
            rows.append({"bound": label, "test": f"{r['test_id']} · {r['investigation']}",
                         "relevance": r["relevance"], "o2": r.get("o2_percent")})
    if not rows:
        return None
    d = pd.DataFrame(rows)
    fig = px.bar(d, x="relevance", y="test", color="bound", orientation="h",
                 color_discrete_map={"Microgravity (0 g)": FLAME, "Normal gravity (1 g)": BLUE},
                 labels={"relevance": "Similarity to selected conditions", "test": ""},
                 hover_data={"o2": True})
    fig.update_layout(**LAYOUT, title="Closest tests at each gravity bound", height=320)
    fig.update_xaxes(range=[0, 1])
    return fig
