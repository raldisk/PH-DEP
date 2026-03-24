"""Unit tests for processor modules — sentiment, enrichment, aggregator."""

from __future__ import annotations

from datetime import datetime, timezone

import pytest

from ph_sentiment.models import TweetEvent


def make_tweet(text: str, tweet_id: str = "1", topic: str = None,
               sentiment: str = None) -> TweetEvent:
    return TweetEvent(
        tweet_id=tweet_id,
        created_at=datetime.now(timezone.utc),
        text=text,
        source="test",
        topic_name=topic,
        sentiment_label=sentiment,
    )


class TestEnrichment:
    def test_extracts_hashtags(self):
        from ph_sentiment.processor.enrichment import enrich_tweet
        tweet = make_tweet("Hello #PHElections and #Pilipinas!")
        result = enrich_tweet(tweet)
        assert "PHElections" in result.hashtags
        assert "Pilipinas" in result.hashtags

    def test_extracts_mentions(self):
        from ph_sentiment.processor.enrichment import enrich_tweet
        tweet = make_tweet("Hey @NDRRMC please update!")
        result = enrich_tweet(tweet)
        assert "NDRRMC" in result.mentions

    def test_does_not_overwrite_existing_hashtags(self):
        from ph_sentiment.processor.enrichment import enrich_tweet
        tweet = make_tweet("#Existing text", tweet_id="2")
        tweet.hashtags = ["PreExisting"]
        result = enrich_tweet(tweet)
        assert result.hashtags == ["PreExisting"]

    def test_adds_utc_timezone_if_missing(self):
        from ph_sentiment.processor.enrichment import enrich_tweet
        tweet = make_tweet("test")
        tweet.created_at = datetime(2024, 1, 1, 12, 0, 0)  # naive
        result = enrich_tweet(tweet)
        assert result.created_at.tzinfo is not None

    def test_enrich_batch(self):
        from ph_sentiment.processor.enrichment import enrich_batch
        tweets = [make_tweet(f"#Tag{i} text", tweet_id=str(i)) for i in range(5)]
        results = enrich_batch(tweets)
        assert len(results) == 5
        assert all(len(r.hashtags) > 0 for r in results)

    def test_top_hashtags(self):
        from ph_sentiment.processor.enrichment import extract_top_hashtags
        tweets = [make_tweet("", tweet_id=str(i)) for i in range(3)]
        tweets[0].hashtags = ["PHElections", "Pilipinas"]
        tweets[1].hashtags = ["PHElections"]
        tweets[2].hashtags = ["Typhoon"]
        top = extract_top_hashtags(tweets, top_n=2)
        assert top[0][0] == "phelections"
        assert top[0][1] == 2


class TestAggregator:
    def test_aggregate_groups_by_window_and_topic(self):
        from ph_sentiment.processor.aggregator import aggregate
        dt = datetime(2024, 1, 15, 10, 3, 0, tzinfo=timezone.utc)
        tweets = [
            make_tweet("pos tweet", "1", topic="PHElections", sentiment="positive"),
            make_tweet("neg tweet", "2", topic="PHElections", sentiment="negative"),
            make_tweet("neu tweet", "3", topic="Typhoon", sentiment="neutral"),
        ]
        for t in tweets:
            t.created_at = dt
        buckets = aggregate(tweets)
        assert len(buckets) == 2
        ph = next(b for b in buckets if b.topic_name == "PHElections")
        assert ph.positive == 1
        assert ph.negative == 1
        assert ph.total == 2

    def test_skips_tweets_without_topic_or_sentiment(self):
        from ph_sentiment.processor.aggregator import aggregate
        tweets = [
            make_tweet("no topic", "1", sentiment="positive"),
            make_tweet("no sentiment", "2", topic="Test"),
        ]
        buckets = aggregate(tweets)
        assert len(buckets) == 0

    def test_sentiment_score_calculation(self):
        from ph_sentiment.processor.aggregator import WindowBucket
        b = WindowBucket(
            window_start=datetime.now(timezone.utc),
            topic_name="test",
            positive=3, neutral=1, negative=1, total=5
        )
        assert b.sentiment_score == pytest.approx(0.4)

    def test_floor_to_window(self):
        from ph_sentiment.processor.aggregator import floor_to_window
        dt = datetime(2024, 1, 15, 10, 7, 30, tzinfo=timezone.utc)
        floored = floor_to_window(dt, window_minutes=5)
        assert floored.minute == 5
        assert floored.second == 0

    def test_top_topics_by_volume(self):
        from ph_sentiment.processor.aggregator import WindowBucket, top_topics_by_volume
        from datetime import datetime, timezone
        dt = datetime.now(timezone.utc)
        buckets = [
            WindowBucket(window_start=dt, topic_name="A", total=100),
            WindowBucket(window_start=dt, topic_name="B", total=50),
            WindowBucket(window_start=dt, topic_name="A", total=30),
        ]
        top = top_topics_by_volume(buckets, top_n=2)
        assert top[0] == ("A", 130)
        assert top[1] == ("B", 50)


class TestSentiment:
    def test_classify_single_via_vader(self):
        """VADER fallback should always be available without GPU/model download."""
        from unittest.mock import patch
        with patch("ph_sentiment.processor.sentiment._get_pipeline", return_value=None):
            from ph_sentiment.processor.sentiment import classify_single
            label, score = classify_single("This is wonderful! I love it!")
            assert label in ("positive", "neutral", "negative")
            assert -1.0 <= score <= 1.0

    def test_classify_batch_returns_all_tweets(self):
        from unittest.mock import patch
        with patch("ph_sentiment.processor.sentiment._get_pipeline", return_value=None):
            from ph_sentiment.processor.sentiment import classify_batch
            tweets = [make_tweet(f"tweet {i}", str(i)) for i in range(5)]
            results = classify_batch(tweets)
            assert len(results) == 5
            assert all(t.sentiment_label is not None for t in results)

    def test_classify_empty_batch(self):
        from ph_sentiment.processor.sentiment import classify_batch
        assert classify_batch([]) == []
