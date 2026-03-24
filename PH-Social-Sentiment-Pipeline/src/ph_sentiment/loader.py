"""
PostgreSQL upsert loader + schema DDL.
All inserts use ON CONFLICT DO UPDATE — re-running is always safe.
"""

from __future__ import annotations

import logging
from typing import Sequence

import psycopg2
import psycopg2.extras

from ph_sentiment.config import settings
from ph_sentiment.models import TrendSnapshot, TweetEvent

logger = logging.getLogger(__name__)

DDL = """
CREATE SCHEMA IF NOT EXISTS raw;

CREATE TABLE IF NOT EXISTS raw.trend_snapshots (
    id              BIGSERIAL    PRIMARY KEY,
    captured_at     TIMESTAMPTZ  NOT NULL,
    topic_name      VARCHAR(280) NOT NULL,
    tweet_volume    INTEGER,
    query           VARCHAR(280),
    region          VARCHAR(10)  DEFAULT 'PH',
    source          VARCHAR(50)  NOT NULL,
    loaded_at       TIMESTAMPTZ  DEFAULT NOW(),
    UNIQUE (captured_at, topic_name, region)
);

CREATE TABLE IF NOT EXISTS raw.tweet_events (
    tweet_id        VARCHAR(30)  PRIMARY KEY,
    created_at      TIMESTAMPTZ  NOT NULL,
    text            TEXT         NOT NULL,
    author_id       VARCHAR(30),
    lang            VARCHAR(10),
    hashtags        TEXT[],
    mentions        TEXT[],
    source          VARCHAR(50)  NOT NULL,
    sentiment_label VARCHAR(20),
    sentiment_score NUMERIC(5,4),
    topic_name      VARCHAR(280),
    loaded_at       TIMESTAMPTZ  DEFAULT NOW()
);

CREATE INDEX IF NOT EXISTS idx_trend_captured_at
    ON raw.trend_snapshots (captured_at DESC);

CREATE INDEX IF NOT EXISTS idx_tweet_created_at
    ON raw.tweet_events (created_at DESC);

CREATE INDEX IF NOT EXISTS idx_tweet_topic
    ON raw.tweet_events (topic_name);
"""


def get_connection() -> psycopg2.extensions.connection:
    return psycopg2.connect(settings.postgres_dsn)


def ensure_schema() -> None:
    with get_connection() as conn:
        with conn.cursor() as cur:
            cur.execute(DDL)
        conn.commit()
    logger.info("Schema ensured.")


def upsert_trends(records: Sequence[TrendSnapshot]) -> int:
    if not records:
        return 0
    rows = [
        (r.captured_at, r.topic_name, r.tweet_volume, r.query, r.region, r.source)
        for r in records
    ]
    sql = """
        INSERT INTO raw.trend_snapshots
            (captured_at, topic_name, tweet_volume, query, region, source)
        VALUES %s
        ON CONFLICT (captured_at, topic_name, region)
        DO UPDATE SET tweet_volume = EXCLUDED.tweet_volume, loaded_at = NOW()
    """
    with get_connection() as conn:
        with conn.cursor() as cur:
            psycopg2.extras.execute_values(cur, sql, rows)
        conn.commit()
    logger.info("Upserted %d trend snapshots.", len(rows))
    return len(rows)


def upsert_tweets(records: Sequence[TweetEvent]) -> int:
    if not records:
        return 0
    rows = [
        (r.tweet_id, r.created_at, r.text, r.author_id, r.lang,
         r.hashtags, r.mentions, r.source,
         r.sentiment_label, r.sentiment_score, r.topic_name)
        for r in records
    ]
    sql = """
        INSERT INTO raw.tweet_events
            (tweet_id, created_at, text, author_id, lang,
             hashtags, mentions, source,
             sentiment_label, sentiment_score, topic_name)
        VALUES %s
        ON CONFLICT (tweet_id)
        DO UPDATE SET
            sentiment_label = EXCLUDED.sentiment_label,
            sentiment_score = EXCLUDED.sentiment_score,
            topic_name      = EXCLUDED.topic_name,
            loaded_at       = NOW()
    """
    with get_connection() as conn:
        with conn.cursor() as cur:
            psycopg2.extras.execute_values(cur, sql, rows)
        conn.commit()
    logger.info("Upserted %d tweet events.", len(rows))
    return len(rows)


def row_counts() -> dict[str, int]:
    tables = ["raw.trend_snapshots", "raw.tweet_events"]
    counts = {}
    with get_connection() as conn:
        with conn.cursor() as cur:
            for t in tables:
                cur.execute(f"SELECT COUNT(*) FROM {t}")
                counts[t] = cur.fetchone()[0]
    return counts
