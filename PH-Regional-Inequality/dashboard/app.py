"""
Philippine Regional Inequality Dashboard — Streamlit app.

Reads from PostgreSQL raw tables:
  raw.poverty_provincial     — regional poverty incidence 2018/2021/2023
  raw.fies_2023              — family income and expenditure
  raw.grdp_regional          — gross regional domestic product
  raw.poverty_sae_municipal  — municipal-level SAE poverty data

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
    page_title="PH Regional Inequality",
    page_icon="🇵🇭",
    layout="wide",
    initial_sidebar_state="expanded",
)

DSN = os.environ.get("DATABASE_URL", "postgresql://inequality:inequality@localhost:5432/ph_inequality")


@st.cache_data(ttl=600)
def load_poverty() -> pd.DataFrame:
    with psycopg2.connect(DSN) as conn:
        return pd.read_sql(
            "SELECT * FROM raw.poverty_provincial WHERE province_code IS NULL ORDER BY region_name",
            conn,
        )


@st.cache_data(ttl=600)
def load_fies() -> pd.DataFrame:
    with psycopg2.connect(DSN) as conn:
        return pd.read_sql("SELECT * FROM raw.fies_2023", conn)


@st.cache_data(ttl=600)
def load_grdp() -> pd.DataFrame:
    with psycopg2.connect(DSN) as conn:
        return pd.read_sql("SELECT * FROM raw.grdp_regional ORDER BY year, region_code", conn)


@st.cache_data(ttl=600)
def load_sae() -> pd.DataFrame:
    with psycopg2.connect(DSN) as conn:
        return pd.read_sql("SELECT * FROM raw.poverty_sae_municipal", conn)


# ── Sidebar ───────────────────────────────────────────────────────────────────
st.sidebar.title("🇵🇭 PH Regional Inequality")
st.sidebar.caption("PSA FIES 2023 · Census 2020 · Poverty Statistics 2023")

try:
    poverty_df = load_poverty()
    fies_df    = load_fies()
    grdp_df    = load_grdp()
    sae_df     = load_sae()
except Exception as e:
    st.error(f"Database connection failed: {e}")
    st.info("Run `python scripts/download_data.py --generate-sample` then load into PostgreSQL.")
    st.stop()

all_regions = sorted(poverty_df["region_name"].unique())
selected_regions = st.sidebar.multiselect(
    "Filter regions", all_regions, default=all_regions[:5]
)
year_filter = st.sidebar.selectbox("Poverty year", [2023, 2021, 2018], index=0)

# ── Header metrics ────────────────────────────────────────────────────────────
st.markdown("### Key National Indicators")
c1, c2, c3, c4 = st.columns(4)
c1.metric("National Gini 2023", "0.387", "−0.013 vs 2021", delta_color="inverse")
c2.metric("Below 0.40 threshold", "First time ever (2023)")
c3.metric("LGUs below 20% poverty", "54.7% of 1,611")
c4.metric("BARMM improvement", "−24pp (2021→2023)", delta_color="inverse")

st.divider()

# ── Poverty incidence chart ───────────────────────────────────────────────────
st.markdown("### Poverty Incidence by Region")
pov_year = poverty_df[poverty_df["year"] == year_filter].sort_values(
    "poverty_incidence", ascending=True
)
fig1 = px.bar(
    pov_year, x="poverty_incidence", y="region_name",
    orientation="h", color="poverty_incidence",
    color_continuous_scale="RdYlGn_r",
    labels={"poverty_incidence": "Poverty incidence (%)", "region_name": "Region"},
    title=f"Poverty Incidence by Region — PSA {year_filter}",
)
fig1.add_vline(x=20, line_dash="dash", line_color="#e09932",
               annotation_text="National avg ~20%")
fig1.update_layout(height=500, showlegend=False,
                   plot_bgcolor="rgba(0,0,0,0)", paper_bgcolor="rgba(0,0,0,0)")
st.plotly_chart(fig1, use_container_width=True)

st.divider()

# ── Income distribution + GRDP ────────────────────────────────────────────────
col_left, col_right = st.columns(2)

with col_left:
    st.markdown("### Mean Family Income by Region (FIES 2023)")
    income_reg = fies_df.groupby("region_name")["total_income_php"].mean().reset_index()
    income_reg = income_reg.sort_values("total_income_php")
    fig2 = px.bar(
        income_reg, x="total_income_php", y="region_name",
        orientation="h", color="total_income_php",
        color_continuous_scale="Blues",
        labels={"total_income_php": "Mean family income (PHP/yr)", "region_name": "Region"},
    )
    fig2.update_layout(height=420, showlegend=False,
                       plot_bgcolor="rgba(0,0,0,0)", paper_bgcolor="rgba(0,0,0,0)")
    st.plotly_chart(fig2, use_container_width=True)

with col_right:
    st.markdown("### GRDP Growth by Region (2023)")
    grdp_2023 = grdp_df[grdp_df["year"] == 2023].sort_values("grdp_growth_pct")
    fig3 = px.bar(
        grdp_2023, x="grdp_growth_pct", y="region_name",
        orientation="h",
        color="grdp_growth_pct",
        color_continuous_scale="RdYlGn",
        labels={"grdp_growth_pct": "GRDP growth %", "region_name": "Region"},
    )
    fig3.update_layout(height=420, showlegend=False,
                       plot_bgcolor="rgba(0,0,0,0)", paper_bgcolor="rgba(0,0,0,0)")
    st.plotly_chart(fig3, use_container_width=True)

st.divider()

# ── SAE distribution ──────────────────────────────────────────────────────────
st.markdown("### SAE Poverty Distribution — 1,611 LGUs")
fig4 = px.histogram(
    sae_df, x="poverty_incidence", nbins=30,
    color_discrete_sequence=["#4c8ed4"],
    labels={"poverty_incidence": "Poverty incidence (%)", "count": "Number of LGUs"},
    title="Distribution of Municipal Poverty Incidence — PSA SAE 2023",
)
fig4.add_vline(x=20, line_dash="dash", line_color="#e09932",
               annotation_text="20% threshold")
fig4.update_layout(plot_bgcolor="rgba(0,0,0,0)", paper_bgcolor="rgba(0,0,0,0)")
st.plotly_chart(fig4, use_container_width=True)

st.divider()
st.caption(
    "Data: PSA Poverty Statistics 2023 · PSA FIES 2023 · PSA Census 2020 · PSA OpenSTAT (GRDP) · "
    "World Bank WDI · GADM boundaries"
)
