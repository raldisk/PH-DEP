"""Unit tests for loader module — all DB calls mocked."""

from __future__ import annotations

from datetime import datetime, timezone
from unittest.mock import MagicMock, patch

import pytest

from ph_sentiment.models import TrendSnapshot, TweetEvent


def make_trend(name: str = "#PHElections") -> TrendSnapshot:
    return TrendSnapshot(
        captured_at=datetime.now(timezone.utc),
        topic_name=name,
        tweet_volume=1000,
        source="simulator",
    )


def make_tweet(tweet_id: str = "1") -> TweetEvent:
    return TweetEvent(
        tweet_id=tweet_id,
        created_at=datetime.now(timezone.utc),
        text="Sample tweet text",
        source="simulator",
        sentiment_label="positive",
        sentiment_score=0.85,
    )


class TestUpsertTrends:
    def test_empty_list_returns_zero(self):
        from ph_sentiment.loader import upsert_trends
        with patch("ph_sentiment.loader.get_connection"):
            assert upsert_trends([]) == 0

    def test_returns_count(self):
        mock_conn = MagicMock()
        mock_conn.__enter__ = MagicMock(return_value=mock_conn)
        mock_conn.__exit__ = MagicMock(return_value=False)
        mock_conn.cursor.return_value.__enter__ = MagicMock(
            return_value=mock_conn.cursor.return_value
        )
        mock_conn.cursor.return_value.__exit__ = MagicMock(return_value=False)

        with patch("ph_sentiment.loader.get_connection", return_value=mock_conn):
            with patch("ph_sentiment.loader.psycopg2.extras.execute_values"):
                from ph_sentiment.loader import upsert_trends
                result = upsert_trends([make_trend(), make_trend("#Pilipinas")])
        assert result == 2


class TestUpsertTweets:
    def test_empty_list_returns_zero(self):
        from ph_sentiment.loader import upsert_tweets
        with patch("ph_sentiment.loader.get_connection"):
            assert upsert_tweets([]) == 0

    def test_returns_count(self):
        mock_conn = MagicMock()
        mock_conn.__enter__ = MagicMock(return_value=mock_conn)
        mock_conn.__exit__ = MagicMock(return_value=False)
        mock_conn.cursor.return_value.__enter__ = MagicMock(
            return_value=mock_conn.cursor.return_value
        )
        mock_conn.cursor.return_value.__exit__ = MagicMock(return_value=False)

        with patch("ph_sentiment.loader.get_connection", return_value=mock_conn):
            with patch("ph_sentiment.loader.psycopg2.extras.execute_values"):
                from ph_sentiment.loader import upsert_tweets
                result = upsert_tweets([make_tweet("1"), make_tweet("2"), make_tweet("3")])
        assert result == 3


class TestRowCounts:
    @pytest.mark.integration
    def test_row_counts_returns_dict(self):
        from ph_sentiment.loader import row_counts
        counts = row_counts()
        assert isinstance(counts, dict)
        assert "raw.trend_snapshots" in counts
        assert "raw.tweet_events" in counts
