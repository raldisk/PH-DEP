"""Unit tests for Pydantic v2 domain models."""

from __future__ import annotations

from datetime import datetime, timezone

import pytest
from pydantic import ValidationError

from ph_sentiment.models import TrendSnapshot, TweetEvent


class TestTrendSnapshot:
    def test_valid(self):
        t = TrendSnapshot(
            captured_at=datetime(2024, 1, 1, tzinfo=timezone.utc),
            topic_name="#PHElections",
            tweet_volume=50000,
            source="simulator",
        )
        assert t.topic_name == "#PHElections"

    def test_strips_whitespace(self):
        t = TrendSnapshot(
            captured_at=datetime(2024, 1, 1, tzinfo=timezone.utc),
            topic_name="  #PHElections  ",
            source="simulator",
        )
        assert t.topic_name == "#PHElections"

    def test_rejects_empty_topic(self):
        with pytest.raises(ValidationError):
            TrendSnapshot(
                captured_at=datetime(2024, 1, 1, tzinfo=timezone.utc),
                topic_name="",
                source="simulator",
            )

    def test_negative_volume_becomes_none(self):
        t = TrendSnapshot(
            captured_at=datetime(2024, 1, 1, tzinfo=timezone.utc),
            topic_name="#Test",
            tweet_volume=-1,
            source="simulator",
        )
        assert t.tweet_volume is None

    def test_optional_volume_allowed(self):
        t = TrendSnapshot(
            captured_at=datetime(2024, 1, 1, tzinfo=timezone.utc),
            topic_name="#Test",
            source="simulator",
        )
        assert t.tweet_volume is None


class TestTweetEvent:
    def test_valid(self, sample_tweet):
        assert sample_tweet.tweet_id == "1001"
        assert "WeLoveTheEarth" in sample_tweet.text

    def test_valid_sentiment_labels(self):
        for label in ("positive", "neutral", "negative"):
            t = TweetEvent(
                tweet_id="x", created_at=datetime(2024,1,1,tzinfo=timezone.utc),
                text="test", source="simulator", sentiment_label=label,
            )
            assert t.sentiment_label == label

    def test_rejects_invalid_sentiment(self):
        with pytest.raises(ValidationError):
            TweetEvent(
                tweet_id="x", created_at=datetime(2024,1,1,tzinfo=timezone.utc),
                text="test", source="simulator", sentiment_label="happy",
            )

    def test_empty_text_rejected(self):
        with pytest.raises(ValidationError):
            TweetEvent(
                tweet_id="x", created_at=datetime(2024,1,1,tzinfo=timezone.utc),
                text="", source="simulator",
            )

    def test_default_lists(self, sample_tweet):
        assert sample_tweet.hashtags == []
        assert sample_tweet.mentions == []
