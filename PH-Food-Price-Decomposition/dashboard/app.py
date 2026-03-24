"""
PH Food Price Inflation Dashboard — Streamlit app.

Reads from PostgreSQL:
  raw.psa_price_situationer  — commodity prices
  raw.doe_fuel_prices        — diesel/gasoline/LPG
  raw.stl_residuals          — STL decomposition output (from notebook 05)

Run locally:
  streamlit run dashboard/app.py
"""

from __future__ import annotations

import os

import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
import psycopg2
import streamlit as st
from plotly.subplots import make_subplots

st.set_page_config(
    page_title="PH Food Price Decomposition",
    page_icon="🇵🇭",
    layout="wide",
    initial_sidebar_state="expanded",
)

DSN = os.environ.get("DATABASE_URL", "postgresql://food:food@localhost:5432/ph_food_prices")

COMMODITIES = [
    "rice_wellmilled", "rice_regular", "pork_lean", "beef_lean",
    "fish_galunggong", "cooking_oil", "onion_white", "tomato", "cabbage",
]


@st.cache_data(ttl=600)
def load_prices(commodity: str) -> pd.DataFrame:
    with psycopg2.connect(DSN) as conn:
        return pd.read_sql(f"""
            SELECT DATE_TRUNC('month', price_date)::DATE AS month,
                   AVG(retail_price_php) AS avg_price,
                   STDDEV(retail_price_php) AS std_price
            FROM raw.psa_price_situationer
            WHERE commodity_slug = '{commodity}' AND region = 'National'
            GROUP BY 1 ORDER BY 1
        """, conn, parse_dates=["month"])


@st.cache_data(ttl=600)
def load_fuel() -> pd.DataFrame:
    with psycopg2.connect(DSN) as conn:
        return pd.read_sql("""
            SELECT DATE_TRUNC('month', price_date)::DATE AS month,
                   fuel_type, AVG(price_php) AS avg_price
            FROM raw.doe_fuel_prices
            GROUP BY 1, 2 ORDER BY 1
        """, conn, parse_dates=["month"])


@st.cache_data(ttl=600)
def load_stl(commodity: str) -> pd.DataFrame:
    try:
        with psycopg2.connect(DSN) as conn:
            return pd.read_sql(f"""
                SELECT month, trend, seasonal, residual
                FROM raw.stl_residuals
                WHERE commodity_slug = '{commodity}'
                ORDER BY month
            """, conn, parse_dates=["month"])
    except Exception:
        return pd.DataFrame()


@st.cache_data(ttl=600)
def load_all_latest() -> pd.DataFrame:
    with psycopg2.connect(DSN) as conn:
        return pd.read_sql("""
            SELECT commodity_slug,
                   AVG(retail_price_php) AS avg_price,
                   STDDEV(retail_price_php) AS std_price
            FROM raw.psa_price_situationer
            WHERE price_date >= CURRENT_DATE - INTERVAL '6 months'
              AND region = 'National'
            GROUP BY commodity_slug
            ORDER BY avg_price DESC
        """, conn)


# ── Sidebar ───────────────────────────────────────────────────────────────────
st.sidebar.title("🇵🇭 PH Food Price Dashboard")
st.sidebar.caption("PSA Price Situationer · DOE Oil Monitor · 2000–2026")

selected = st.sidebar.selectbox(
    "Select commodity",
    COMMODITIES,
    format_func=lambda x: x.replace("_", " ").title(),
)
year_range = st.sidebar.slider("Year range", 2000, 2026, (2010, 2026))

# ── Header ────────────────────────────────────────────────────────────────────
st.markdown("### Key Food Price Indicators (last 6 months)")

try:
    latest_df = load_all_latest()
    cols = st.columns(4)
    for i, row in latest_df.head(4).iterrows():
        cols[i % 4].metric(
            row["commodity_slug"].replace("_", " ").title(),
            f"₱{row['avg_price']:.2f}/kg",
        )

    st.divider()
    df = load_prices(selected)
    fuel_df = load_fuel()
    db_ok = True
except Exception as e:
    st.error(f"Database connection failed: {e}")
    st.info("Run `python scripts/scrape_psa_prices.py --generate-sample` then load into PostgreSQL.")
    st.stop()

# ── Filter by year ────────────────────────────────────────────────────────────
df_f = df[df["month"].dt.year.between(*year_range)]

# ── Main price chart ──────────────────────────────────────────────────────────
st.markdown(f"### {selected.replace('_', ' ').title()} — Retail Price Trend")

fig = go.Figure()
fig.add_trace(go.Scatter(
    x=df_f["month"], y=df_f["avg_price"],
    name="Monthly avg", line=dict(color="#4c8ed4", width=2),
    fill="tozeroy", fillcolor="rgba(76,142,212,0.07)",
))

if "std_price" in df_f.columns:
    fig.add_trace(go.Scatter(
        x=pd.concat([df_f["month"], df_f["month"].iloc[::-1]]),
        y=pd.concat([df_f["avg_price"] + df_f["std_price"],
                     (df_f["avg_price"] - df_f["std_price"]).iloc[::-1]]),
        fill="toself", fillcolor="rgba(76,142,212,0.1)",
        line=dict(color="rgba(0,0,0,0)"), name="±1 std dev",
    ))

# Policy event annotations
for date_str, label, color in [
    ("2019-03-01", "RTL (2019)", "#3da679"),
    ("2020-03-01", "COVID ECQ", "#e24b4a"),
    ("2023-01-01", "Onion crisis", "#e09932"),
    ("2022-02-01", "Ukraine war", "#a78bfa"),
]:
    fig.add_vline(x=pd.Timestamp(date_str), line_dash="dash",
                  line_color=color, opacity=0.6,
                  annotation_text=label, annotation_font_color=color)

fig.update_layout(height=380, hovermode="x unified",
                  plot_bgcolor="rgba(0,0,0,0)", paper_bgcolor="rgba(0,0,0,0)")
fig.update_yaxes(title_text="₱ per kg")
st.plotly_chart(fig, use_container_width=True)

st.divider()

# ── STL decomposition (if available) ─────────────────────────────────────────
stl_df = load_stl(selected)
col_left, col_right = st.columns(2)

with col_left:
    if not stl_df.empty:
        st.markdown("### STL Decomposition")
        stl_f = stl_df[stl_df["month"].dt.year.between(*year_range)]
        fig2 = make_subplots(rows=3, cols=1, shared_xaxes=True,
                             subplot_titles=["Trend", "Seasonal", "Residual"])
        colors = ["#e09932", "#3da679", "#e24b4a"]
        for i, (col, color) in enumerate(zip(["trend","seasonal","residual"], colors), 1):
            fig2.add_trace(go.Scatter(
                x=stl_f["month"], y=stl_f[col],
                line=dict(color=color, width=1.5), showlegend=False,
            ), row=i, col=1)
        fig2.update_layout(height=380, plot_bgcolor="rgba(0,0,0,0)",
                           paper_bgcolor="rgba(0,0,0,0)")
        st.plotly_chart(fig2, use_container_width=True)
    else:
        st.info("STL decomposition not yet run. Execute notebook 05 first.")

with col_right:
    st.markdown("### Diesel Price vs Selected Commodity")
    diesel = fuel_df[fuel_df["fuel_type"] == "diesel"]
    diesel_f = diesel[diesel["month"].dt.year.between(*year_range)]
    df_f2 = df[df["month"].dt.year.between(*year_range)]

    fig3 = make_subplots(specs=[[{"secondary_y": True}]])
    fig3.add_trace(go.Scatter(
        x=df_f2["month"], y=df_f2["avg_price"],
        name=selected.replace("_"," ").title(), line=dict(color="#4c8ed4"),
    ), secondary_y=False)
    fig3.add_trace(go.Scatter(
        x=diesel_f["month"], y=diesel_f["avg_price"],
        name="Diesel ₱/L", line=dict(color="#d85a30", dash="dash"),
    ), secondary_y=True)
    fig3.update_layout(height=380, plot_bgcolor="rgba(0,0,0,0)",
                       paper_bgcolor="rgba(0,0,0,0)")
    fig3.update_yaxes(title_text="₱/kg", secondary_y=False)
    fig3.update_yaxes(title_text="Diesel ₱/L", secondary_y=True)
    st.plotly_chart(fig3, use_container_width=True)

st.divider()
st.caption(
    "Sources: PSA Price Situationer (psa.gov.ph) · DOE Oil Monitor (doe.gov.ph) · "
    "WFP HDX Philippines (data.humdata.org) · World Bank Pink Sheet"
)
