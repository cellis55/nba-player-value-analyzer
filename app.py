"""NBA Value Lab — 2024–25 salary-adjusted production dashboard.

Run from the repository root with: streamlit run app.py
The data is exported by notebooks/04_player_value_model.ipynb.
"""
from pathlib import Path

import numpy as np
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
import streamlit as st

st.set_page_config(page_title="NBA Value Lab | 2024–25", page_icon="🏀", layout="wide", initial_sidebar_state="expanded")

# Consistent styles; Streamlit still owns the interactive widgets.
st.markdown("""
<style>
[data-testid="stAppViewContainer"] { background: #0b1220; color: #eef3ff; }
[data-testid="stSidebar"] { background: #111d30; }
[data-testid="stHeader"] { background: rgba(11,18,32,0.93); }
/* Accessible contrast for Streamlit widgets and supporting text. */
:root { color-scheme: dark; }
[data-testid="stAppViewContainer"] p,
[data-testid="stAppViewContainer"] label,
[data-testid="stAppViewContainer"] span,
[data-testid="stAppViewContainer"] small,
[data-testid="stAppViewContainer"] h1,
[data-testid="stAppViewContainer"] h2,
[data-testid="stAppViewContainer"] h3,
[data-testid="stAppViewContainer"] h4 { color: #e9f1fc; }
[data-testid="stSidebar"] p,
[data-testid="stSidebar"] label,
[data-testid="stSidebar"] span,
[data-testid="stSidebar"] small,
[data-testid="stSidebar"] h2,
[data-testid="stSidebar"] h3 { color: #e6eefb !important; }
[data-testid="stSidebar"] [data-testid="stCaptionContainer"] p,
[data-testid="stAppViewContainer"] [data-testid="stCaptionContainer"] p { color: #b6c6dd !important; }
[data-testid="stTabs"] [role="tab"] { color: #cbd8ed !important; }
[data-testid="stTabs"] [role="tab"][aria-selected="true"] { color: #ffffff !important; }
[data-testid="stTabs"] [role="tab"] p { color: inherit !important; }
[data-testid="stWidgetLabel"] p { color: #dce8f8 !important; }
/* Select inputs should stay dark with readable foreground text. */
[data-baseweb="select"] > div { background-color: #1c2d45 !important; color: #f3f7ff !important; border-color: #46607b !important; }
[data-baseweb="select"] span { color: #f3f7ff !important; }
[data-testid="stMetricLabel"] p { color: #b6c6dd !important; }
/* Streamlit plot and dataframe toolbars remain interactive. */
h1, h2, h3 { letter-spacing: -.025em; }
h1 { font-size: 2.5rem !important; }
[data-testid="stMetric"] { background: #17253a; border: 1px solid #2a3b54; border-radius: 14px; padding: 1rem; }
[data-testid="stMetricLabel"] { color: #a9bbd2; }
[data-testid="stMetricValue"] { color: #f5f8ff; }
div[data-testid="stDataFrame"] { border: 1px solid #2a3b54; border-radius: 12px; overflow: hidden; }
.block-container { padding-top: 5rem !important; max-width: 1350px; }
.subtitle { color: #a9bbd2; font-size: 1.05rem; margin: -.4rem 0 1.4rem 0; }
.eyebrow { display: block; padding-top: .5rem; line-height: 1.8; text-transform: uppercase; letter-spacing: .15em; color: #58c9e8; font-size: .77rem; font-weight: 700; }
.insight { background: #16263c; border: 1px solid #2b4661; border-radius: 14px; padding: 1.1rem 1.3rem; min-height: 130px; }
.insight-label { font-size: .82rem; color: #a9bbd2; }
.insight-title { color: #f6f8ff; font-size: 1.33rem; font-weight: 750; margin: .25rem 0; }
.insight-note { color: #8ee1c7; font-size: .95rem; }
</style>
""", unsafe_allow_html=True)

DATA_PATH = Path(__file__).resolve().parent / "data" / "processed" / "nba_dashboard_data.csv"
REQUIRED = ["player_id", "player_name", "salary_millions", "salary_2024_25", "total_minutes_est", "minutes_per_game", "points_per_game", "rebounds_per_game", "assists_per_game", "steals_per_game", "blocks_per_game", "TS_PCT", "production_score", "expected_production", "value_score", "value_rank"]

@st.cache_data
def load_data():
    data = pd.read_csv(DATA_PATH)
    missing = sorted(set(REQUIRED) - set(data.columns))
    if missing:
        raise ValueError(f"Missing required columns: {', '.join(missing)}")
    if data["player_id"].duplicated().any():
        raise ValueError("Duplicate player IDs in dashboard data")
    return data

try:
    df = load_data()
except Exception as exc:
    st.error(f"Could not load {DATA_PATH}: {exc}")
    st.info("Run Notebook 04 through the dashboard CSV export, then restart the app.")
    st.stop()

# Infer full-precision regression curve from the values exported by Notebook 04,
# rather than hardcoding rounded regression coefficients.
regression_slope, regression_intercept = np.polyfit(
    np.log(df["salary_millions"].to_numpy()), df["expected_production"].to_numpy(), 1
)
model_r2 = 1 - (
    np.square(df["production_score"] - df["expected_production"]).sum()
    / np.square(df["production_score"] - df["production_score"].mean()).sum()
)

CHART_BG = "#0e192b"
CHART_GRID = "#2c3b51"
CHART_TEXT = "#d9e5f3"
ACCENT = "#49c5e6"
GREEN = "#70ddad"

def plot_style(fig, height=510):
    fig.update_layout(
        template="plotly_dark", paper_bgcolor=CHART_BG, plot_bgcolor=CHART_BG,
        font=dict(color=CHART_TEXT), height=height,
        margin=dict(l=18, r=16, t=35, b=20),
        legend=dict(orientation="h", y=1.08),
    )
    fig.update_xaxes(gridcolor=CHART_GRID, zerolinecolor=CHART_GRID)
    fig.update_yaxes(gridcolor=CHART_GRID, zerolinecolor=CHART_GRID)
    return fig

st.markdown('<div class="eyebrow">2024–25 regular season · Interactive analytics</div>', unsafe_allow_html=True)
st.title("NBA Value Lab")
st.markdown('<div class="subtitle">Who delivers the most statistical production relative to their salary?</div>', unsafe_allow_html=True)

with st.sidebar:
    st.header("Explore the data")
    max_salary = st.slider("Maximum salary ($M)", min_value=1, max_value=60, value=60)
    min_minutes = st.select_slider("Minimum season minutes", options=[1000, 1500, 2000], value=1000)
    st.caption("Filters apply to Overview and Value Explorer. Comparisons use the complete 266-player dataset.")
    st.divider()
    st.caption("**Model:** Weighted per-36 statistics + true shooting; regression against log salary.")
    st.caption("**Caution:** Team labels and compensation definitions have remaining historical-data limitations.")

filtered = df.loc[(df.salary_millions <= max_salary) & (df.total_minutes_est >= min_minutes)].copy()
tabs = st.tabs(["Overview", "Value Explorer", "Compare Players", "Methodology"])

with tabs[0]:
    st.subheader("Season at a glance")
    cols = st.columns(4)
    cols[0].metric("Players shown", f"{len(filtered):,}")
    cols[1].metric("Average salary", f"${filtered.salary_millions.mean():.2f}M" if len(filtered) else "—")
    cols[2].metric("Median salary", f"${filtered.salary_millions.median():.2f}M" if len(filtered) else "—")
    cols[3].metric("Full-model R²", f"{model_r2:.3f}")
    st.caption("Salary summary follows the selected filters. R² describes the original fitted sample and does not change with filters.")
    if filtered.empty:
        st.warning("No players match these filters. Raise the salary ceiling or lower the minimum minutes.")
    else:
        best = filtered.nlargest(1, "value_score").iloc[0]
        budget = filtered[filtered.salary_millions < 15]
        left, right = st.columns(2)
        with left:
            st.markdown(f'<div class="insight"><div class="insight-label">Highest salary-adjusted value · selected group</div><div class="insight-title">{best.player_name}</div><div class="insight-note">+{best.value_score:.3f} value score · ${best.salary_millions:.2f}M</div></div>', unsafe_allow_html=True)
        with right:
            if len(budget):
                b = budget.nlargest(1, "value_score").iloc[0]
                st.markdown(f'<div class="insight"><div class="insight-label">Best value under $15M · selected group</div><div class="insight-title">{b.player_name}</div><div class="insight-note">+{b.value_score:.3f} value score · ${b.salary_millions:.2f}M</div></div>', unsafe_allow_html=True)
            else:
                st.info("No players under $15M match these filters.")
        st.markdown("#### Salary vs. production")
        scatter = px.scatter(filtered, x="salary_millions", y="production_score", color="value_score",
            color_continuous_scale="RdYlGn", hover_name="player_name",
            hover_data={"salary_millions": ":.2f", "production_score": ":.3f", "expected_production": ":.3f", "value_score": ":.3f", "points_per_game": ":.1f"},
            labels={"salary_millions": "2024–25 salary ($M)", "production_score": "Production score", "value_score": "Value score"})
        salary_grid = np.linspace(max(filtered.salary_millions.min(), 0.01), filtered.salary_millions.max(), 200)
        scatter.add_trace(go.Scatter(x=salary_grid, y=regression_intercept + regression_slope * np.log(salary_grid),
            mode="lines", name="Expected production", line=dict(color="#ffffff", width=3, dash="dash"), hoverinfo="skip"))
        scatter.update_traces(marker=dict(size=10, opacity=.82), selector=dict(mode="markers"))
        st.plotly_chart(plot_style(scatter, 540), use_container_width=True)
        st.caption("Above the dashed curve = higher production than the model expects at that salary. A higher value score is not a dollar estimate.")
        c1, c2 = st.columns(2)
        with c1:
            st.markdown("#### Top 10 value scores")
            top = filtered.nlargest(10, "value_score").sort_values("value_score")
            bars = px.bar(top, x="value_score", y="player_name", orientation="h",
                labels={"value_score": "Value score", "player_name": ""})
            bars.update_traces(marker_color=ACCENT)
            st.plotly_chart(plot_style(bars, 430), use_container_width=True)
        with c2:
            st.markdown("#### Salary distribution")
            hist = px.histogram(filtered, x="salary_millions", nbins=22,
                labels={"salary_millions": "Salary ($M)", "count": "Players"})
            hist.update_traces(marker_color=GREEN)
            hist.update_yaxes(title="Players")
            st.plotly_chart(plot_style(hist, 430), use_container_width=True)

with tabs[1]:
    st.subheader("Value Explorer")
    st.write("Explore the ranking, switch to budget contracts, or download the current filtered view.")
    mode = st.radio("Leaderboard", ["Overall", "Budget (under $15M)"], horizontal=True)
    selected = filtered.copy()
    if mode.startswith("Budget"):
        selected = selected[selected.salary_millions < 15]
    selected = selected.sort_values("value_score", ascending=False).copy()
    selected.insert(0, "Visible rank", range(1, len(selected) + 1))
    display_cols = ["Visible rank", "value_rank", "player_name", "salary_millions", "points_per_game", "rebounds_per_game", "assists_per_game", "TS_PCT", "production_score", "value_score"]
    st.dataframe(selected[display_cols], hide_index=True, use_container_width=True,
        column_config={"Visible rank": "Filtered rank", "value_rank": "Overall rank", "player_name": "Player",
            "salary_millions": st.column_config.NumberColumn("Salary ($M)", format="%.2f"),
            "points_per_game": st.column_config.NumberColumn("PPG", format="%.1f"),
            "rebounds_per_game": st.column_config.NumberColumn("RPG", format="%.1f"),
            "assists_per_game": st.column_config.NumberColumn("APG", format="%.1f"),
            "TS_PCT": st.column_config.NumberColumn("TS (fraction)", format="%.3f"),
            "production_score": st.column_config.NumberColumn("Production", format="%.3f"),
            "value_score": st.column_config.NumberColumn("Value", format="%.3f")})
    st.download_button("Download filtered rankings (CSV)", data=selected[display_cols].to_csv(index=False).encode("utf-8"), file_name="nba_value_filtered.csv", mime="text/csv")
    st.caption("Filtered rank is re-numbered for the current view; Overall rank comes from the unfiltered model.")

with tabs[2]:
    st.subheader("Compare two players")
    names = sorted(df.player_name.unique().tolist())
    p1_col, p2_col = st.columns(2)
    default1 = names.index("Jalen Williams") if "Jalen Williams" in names else 0
    default2 = names.index("Ty Jerome") if "Ty Jerome" in names else min(1, len(names) - 1)
    with p1_col:
        p1 = st.selectbox("First player", names, index=default1)
    with p2_col:
        p2 = st.selectbox("Second player", names, index=default2)
    if p1 == p2:
        st.info("Choose two different players for a meaningful comparison.")
    players_selected = df.set_index("player_name").loc[[p1, p2]]
    left, right = st.columns(2)
    for col, name in zip([left, right], [p1, p2]):
        r = df.loc[df.player_name == name].iloc[0]
        with col:
            st.markdown(f"#### {name}")
            a, b = st.columns(2)
            a.metric("Salary", f"${r.salary_millions:.2f}M")
            b.metric("Value score", f"{r.value_score:+.3f}")
            a2, b2 = st.columns(2)
            a2.metric("Production", f"{r.production_score:.3f}")
            b2.metric("Overall rank", f"#{int(r.value_rank)}")
    labels = {"points_per_game": "Points", "rebounds_per_game": "Rebounds", "assists_per_game": "Assists", "steals_per_game": "Steals", "blocks_per_game": "Blocks"}
    compare = players_selected[list(labels)].rename(columns=labels).reset_index().melt(id_vars="player_name", var_name="Metric", value_name="Per-game")
    fig = px.bar(compare, x="Metric", y="Per-game", color="player_name", barmode="group", color_discrete_sequence=[ACCENT, GREEN], labels={"player_name": "Player"})
    st.plotly_chart(plot_style(fig, 470), use_container_width=True)
    st.caption("Per-game box-score statistics are shown separately from value score so different measurement units aren't mixed on the same axis.")
    st.markdown("#### Efficiency and usage context")
    compare_table = players_selected[["games_played", "minutes_per_game", "TS_PCT", "salary_millions", "value_score"]].copy()
    compare_table["TS_PCT"] = compare_table["TS_PCT"] * 100
    compare_table = compare_table.rename(columns={"games_played": "Games", "minutes_per_game": "Minutes/game", "TS_PCT": "True shooting (%)", "salary_millions": "Salary ($M)", "value_score": "Value score"})
    st.dataframe(compare_table, use_container_width=True)

with tabs[3]:
    st.subheader("How the model works")
    st.markdown("""
    **Question:** Which 2024–25 NBA players produced more box-score output than typically expected at their salary?

    **Sample:** 266 player-season records with roughly 1,000+ season minutes and matched salaries at least $1M. Salaries below $1M were flagged and excluded pending contract comparability review.

    **Production:** We convert points, assists, rebounds, steals, and blocks to per-36-minute statistics, standardize those statistics and true shooting percentage into z-scores, then take a weighted sum.

    | Feature | Weight |
    |---|---:|
    | Points per 36 | 30% |
    | Assists per 36 | 20% |
    | Rebounds per 36 | 15% |
    | Steals per 36 | 10% |
    | Blocks per 36 | 5% |
    | True shooting percentage | 20% |

    **Salary baseline:** An in-sample linear regression predicts production from the natural log of salary in millions.

    **Value score = actual production − expected production.** Positive values are higher-than-expected *relative statistical production*, not estimated contract surplus in dollars.
    """)
    st.latex(r"\widehat{P}=\beta_0+\beta_1\ln(\mathrm{salary}_{\mathrm{millions}})")
    st.write(f"Fitted coefficients inferred from saved expected-production values: intercept **{regression_intercept:.4f}**, slope **{regression_slope:.4f}**; in-sample R² **{model_r2:.4f}**.")
    st.warning("Model limitations: subjective metric weights, no on/off or tracking defense, role and age differences, historical team labels may not reflect the 2024–25 team, rookie-scale contracts, and possible partial-season salary definitions. This is descriptive, not a forecast or definitive contract valuation.")
    st.markdown("**Source and reproducibility:** Player-season statistics were collected through `nba_api`; compensation came from a historical public salary CSV. See the project's notebook pipeline and README for source attribution and the remaining salary audit.")

st.divider()
st.caption("NBA Value Lab · Built with Python, Pandas, scikit-learn, Plotly & Streamlit · Exploratory, non-official NBA analysis")
