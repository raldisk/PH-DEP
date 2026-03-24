"""
PH Social Media Sentiment Dashboard — Streamlit app.
Auto-refreshes every 60 seconds.

Reads from PostgreSQL mart tables:
  marts.trending_topics   — top topics + sentiment score + velocity
  marts.sentiment_hourly  — hourly sentiment breakdown per topic
  marts.keyword_volume    — top hashtags and mentions

Run locally:
  streamlit run dashboard/app.py

Run via Docker:
  docker compose up streamlit
"""

from __future__ import annotations

import os
import time
from datetime import datetime, timedelta

import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
import psycopg2
import streamlit as st
from plotly.subplots import make_subplots

st.set_page_config(
    page_title="PH Sentiment Pipeline",
    page_icon="🇵🇭",
    layout="wide",
    initial_sidebar_state="expanded",
)

DSN = os.environ.get(
    "PH_SENTIMENT_POSTGRES_DSN",
    "postgresql://sentiment:sentiment@localhost:5432/ph_sentiment",
)

REFRESH_INTERVAL = 60  # seconds


@st.cache_data(ttl=REFRESH_INTERVAL)
def load_trending(days: int = 1) -> pd.DataFrame:
    with psycopg2.connect(DSN) as conn:
        return pd.read_sql(
            f"""SELECT * FROM marts.trending_topics
                WHERE day_manila >= NOW() AT TIME ZONE 'Asia/Manila' - INTERVAL '{days} days'
                ORDER BY day_manila DESC, daily_rank""",
            conn, parse_dates=["day_manila"],
        )


@st.cache_data(ttl=REFRESH_INTERVAL)
def load_sentiment_hourly(topic: str | None = None, hours: int = 24) -> pd.DataFrame:
    where = f"AND topic_name = '{topic}'" if topic else ""
    with psycopg2.connect(DSN) as conn:
        return pd.read_sql(
            f"""SELECT * FROM marts.sentiment_hourly
                WHERE hour_manila >= NOW() AT TIME ZONE 'Asia/Manila' - INTERVAL '{hours} hours'
                {where}
                ORDER BY hour_manila""",
            conn, parse_dates=["hour_manila"],
        )


@st.cache_data(ttl=REFRESH_INTERVAL)
def load_keywords(keyword_type: str = "hashtag", days: int = 1) -> pd.DataFrame:
    with psycopg2.connect(DSN) as conn:
        return pd.read_sql(
            f"""SELECT * FROM marts.keyword_volume
                WHERE keyword_type = '{keyword_type}'
                  AND day_manila >= NOW() AT TIME ZONE 'Asia/Manila' - INTERVAL '{days} days'
                ORDER BY day_manila DESC, daily_rank
                LIMIT 30""",
            conn, parse_dates=["day_manila"],
        )


@st.cache_data(ttl=REFRESH_INTERVAL)
def load_raw_counts() -> dict:
    with psycopg2.connect(DSN) as conn:
        with conn.cursor() as cur:
            cur.execute("SELECT COUNT(*) FROM raw.tweet_events")
            tweets = cur.fetchone()[0]
            cur.execute("SELECT COUNT(*) FROM raw.trend_snapshots")
            trends = cur.fetchone()[0]
    return {"tweets": tweets, "trends": trends}


# ── Sidebar ───────────────────────────────────────────────────────────────────
st.sidebar.title("🇵🇭 PH Sentiment Pipeline")
st.sidebar.caption("Kafka → PostgreSQL → Streamlit")
st.sidebar.caption(f"Auto-refresh every {REFRESH_INTERVAL}s")

mode = st.sidebar.selectbox("Pipeline mode", ["Simulation", "Live (Twitter API)"])
hours_back = st.sidebar.slider("Hours to display", 1, 72, 24)
top_n = st.sidebar.slider("Top N topics", 5, 20, 10)

if st.sidebar.button("🔄 Refresh now"):
    st.cache_data.clear()
    st.rerun()

# ── Load data ─────────────────────────────────────────────────────────────────
try:
    trending_df = load_trending(days=max(1, hours_back // 24))
    hourly_df   = load_sentiment_hourly(hours=hours_back)
    hashtags_df = load_keywords("hashtag")
    mentions_df = load_keywords("mention")
    counts      = load_raw_counts()
    db_ok = True
except Exception as e:
    st.error(f"Database connection failed: {e}")
    st.info("Run `python scripts/run_simulation.py` to populate the database, then refresh.")
    st.stop()

# ── Header metrics ────────────────────────────────────────────────────────────
st.markdown("### Pipeline Status")
c1, c2, c3, c4 = st.columns(4)
c1.metric("Total tweets ingested",  f"{counts['tweets']:,}")
c2.metric("Trend snapshots",         f"{counts['trends']:,}")
c3.metric("Mode",                    mode)
c4.metric("Last refresh",            datetime.now().strftime("%H:%M:%S"))

st.divider()

# ── Top trending topics ───────────────────────────────────────────────────────
st.markdown("### 🔥 Top Trending Topics")

if not trending_df.empty:
    top_topics = (
        trending_df.groupby("topic_name")["tweet_count"].sum()
        .sort_values(ascending=False).head(top_n).reset_index()
    )
    top_topics = top_topics.merge(
        trending_df.groupby("topic_name")["avg_sentiment"].mean().reset_index(),
        on="topic_name"
    )

    fig_topics = make_subplots(specs=[[{"secondary_y": True}]])
    colors = ["#3da679" if s > 0.05 else "#e24b4a" if s < -0.05 else "#8b949e"
              for s in top_topics["avg_sentiment"]]
    fig_topics.add_trace(go.Bar(
        x=top_topics["topic_name"], y=top_topics["tweet_count"],
        name="Tweet volume", marker_color=colors, opacity=0.8,
    ))
    fig_topics.add_trace(go.Scatter(
        x=top_topics["topic_name"], y=top_topics["avg_sentiment"],
        name="Avg sentiment", mode="markers+lines",
        marker=dict(size=8, color="#e09932"),
        line=dict(color="#e09932", width=1.5),
    ), secondary_y=True)
    fig_topics.update_layout(
        height=380, hovermode="x unified",
        plot_bgcolor="rgba(0,0,0,0)", paper_bgcolor="rgba(0,0,0,0)",
        legend=dict(orientation="h", y=-0.2),
    )
    fig_topics.update_yaxes(title_text="Tweet volume", secondary_y=False)
    fig_topics.update_yaxes(title_text="Sentiment score", secondary_y=True)
    st.plotly_chart(fig_topics, use_container_width=True)
else:
    st.info("No trending topic data yet. Run the simulation to populate.")

st.divider()

# ── Hourly sentiment time series ──────────────────────────────────────────────
st.markdown("### 📈 Hourly Sentiment Timeline")

topic_options = ["(all topics)"] + sorted(hourly_df["topic_name"].unique().tolist()) \
    if not hourly_df.empty else ["(all topics)"]
selected_topic = st.selectbox("Filter by topic", topic_options)

if not hourly_df.empty:
    if selected_topic != "(all topics)":
        hourly_filtered = hourly_df[hourly_df["topic_name"] == selected_topic]
    else:
        hourly_filtered = hourly_df.groupby("hour_manila")[
            ["positive","neutral","negative","total"]
        ].sum().reset_index()

    fig_hourly = go.Figure()
    fig_hourly.add_trace(go.Bar(
        x=hourly_filtered.get("hour_manila", hourly_filtered.index),
        y=hourly_filtered["positive"],
        name="Positive", marker_color="#3da679", opacity=0.8,
    ))
    fig_hourly.add_trace(go.Bar(
        x=hourly_filtered.get("hour_manila", hourly_filtered.index),
        y=hourly_filtered["neutral"],
        name="Neutral", marker_color="#8b949e", opacity=0.8,
    ))
    fig_hourly.add_trace(go.Bar(
        x=hourly_filtered.get("hour_manila", hourly_filtered.index),
        y=hourly_filtered["negative"],
        name="Negative", marker_color="#e24b4a", opacity=0.8,
    ))
    fig_hourly.update_layout(
        barmode="stack", height=320,
        plot_bgcolor="rgba(0,0,0,0)", paper_bgcolor="rgba(0,0,0,0)",
        legend=dict(orientation="h", y=-0.2),
    )
    st.plotly_chart(fig_hourly, use_container_width=True)

st.divider()

# ── Keyword cloud (top hashtags + mentions) ───────────────────────────────────
col_l, col_r = st.columns(2)

with col_l:
    st.markdown("### # Top Hashtags")
    if not hashtags_df.empty:
        fig_ht = px.bar(
            hashtags_df.head(20), x="occurrences", y="keyword",
            orientation="h", color="sentiment_tilt",
            color_discrete_map={"positive":"#3da679","negative":"#e24b4a","neutral":"#8b949e"},
        )
        fig_ht.update_layout(height=380, showlegend=True,
                              plot_bgcolor="rgba(0,0,0,0)",
                              paper_bgcolor="rgba(0,0,0,0)")
        st.plotly_chart(fig_ht, use_container_width=True)

with col_r:
    st.markdown("### @ Top Mentions")
    if not mentions_df.empty:
        fig_mn = px.bar(
            mentions_df.head(20), x="occurrences", y="keyword",
            orientation="h", color="sentiment_tilt",
            color_discrete_map={"positive":"#3da679","negative":"#e24b4a","neutral":"#8b949e"},
        )
        fig_mn.update_layout(height=380, showlegend=False,
                              plot_bgcolor="rgba(0,0,0,0)",
                              paper_bgcolor="rgba(0,0,0,0)")
        st.plotly_chart(fig_mn, use_container_width=True)

st.divider()
st.caption(
    "Pipeline: Kafka → Faust processor → PostgreSQL → dbt marts → Streamlit  |  "
    "Sentiment model: cardiffnlp/twitter-xlm-roberta-base-sentiment (Taglish-capable)  |  "
    "Simulation fixtures from DataCamp Real-time Social Media Data project"
)

# Auto-refresh
time.sleep(REFRESH_INTERVAL)
st.rerun()
