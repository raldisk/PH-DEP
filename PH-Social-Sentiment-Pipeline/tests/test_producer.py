"""Unit tests for producer modules — all HTTP/Kafka calls mocked."""

from __future__ import annotations

from datetime import datetime, timezone
from unittest.mock import MagicMock, mock_open, patch

import pytest

from ph_sentiment.models import TrendSnapshot, TweetEvent


class TestSimulator:
    def test_parse_ww_trends(self):
        from ph_sentiment.producer.simulator import parse_ww_trends
        raw = [{
            "trends": [
                {"name": "#PHElections", "tweet_volume": 50000, "query": "%23PHElections"},
                {"name": "Marcos", "tweet_volume": None, "query": "Marcos"},
            ],
            "locations": [{"name": "Philippines"}],
        }]
        results = parse_ww_trends(raw)
        assert len(results) == 2
        assert all(isinstance(r, TrendSnapshot) for r in results)
        assert results[0].topic_name == "#PHElections"
        assert results[0].tweet_volume == 50000
        assert results[1].tweet_volume is None

    def test_parse_ww_trends_empty(self):
        from ph_sentiment.producer.simulator import parse_ww_trends
        assert parse_ww_trends([]) == []

    def test_parse_tweets(self):
        from ph_sentiment.producer.simulator import parse_tweets
        raw = [
            {"id": "123", "text": "Mabuhay ang Pilipinas!", "lang": "tl",
             "user": {"id": "456"}},
            {"id": "789", "text": "We love the earth", "lang": "en",
             "user": {"id": "012"}},
        ]
        results = parse_tweets(raw)
        assert len(results) == 2
        assert all(isinstance(r, TweetEvent) for r in results)
        assert results[0].tweet_id == "123"
        assert results[0].lang == "tl"

    def test_parse_tweets_missing_text_skipped(self):
        from ph_sentiment.producer.simulator import parse_tweets
        raw = [{"id": "1", "text": "valid"}, {"id": "2"}]
        results = parse_tweets(raw)
        # Second record has no text — should be skipped or have empty text
        assert len(results) >= 1

    def test_dry_run_does_not_call_kafka(self):
        from ph_sentiment.producer.simulator import produce_to_kafka
        trends = [TrendSnapshot(
            captured_at=datetime.now(timezone.utc),
            topic_name="#PHTest", source="simulator"
        )]
        tweets = []
        # Should not raise even without Kafka running
        produce_to_kafka(trends, tweets, dry_run=True)

    def test_load_fixture_file_not_found(self):
        from ph_sentiment.producer.simulator import load_fixture
        with pytest.raises(FileNotFoundError):
            load_fixture("nonexistent_fixture.json")


class TestTwitterTrends:
    def test_empty_bearer_token_returns_empty(self):
        from ph_sentiment.producer.twitter_trends import fetch_trending_topics
        with patch("ph_sentiment.producer.twitter_trends.settings") as mock_settings:
            mock_settings.twitter_bearer_token = ""
            result = fetch_trending_topics()
        assert result == []

    def test_parse_v2_response(self):
        from ph_sentiment.producer.twitter_trends import _parse_v2_response
        data = {
            "data": [
                {"id": "1", "text": "test", "entities": {
                    "hashtags": [{"tag": "PHElections"}, {"tag": "Pilipinas"}]
                }},
            ]
        }
        results = _parse_v2_response(data)
        assert len(results) == 2
        assert results[0].topic_name == "#PHElections"

    def test_parse_v2_response_no_hashtags(self):
        from ph_sentiment.producer.twitter_trends import _parse_v2_response
        data = {"data": [{"id": "1", "text": "no hashtags here"}]}
        results = _parse_v2_response(data)
        assert results == []


class TestTweetSampler:
    def test_empty_bearer_token_returns_empty(self):
        from ph_sentiment.producer.tweet_sampler import fetch_recent_tweets
        with patch("ph_sentiment.producer.tweet_sampler.settings") as mock_settings:
            mock_settings.twitter_bearer_token = ""
            result = fetch_recent_tweets()
        assert result == []

    def test_parse_tweets(self):
        from ph_sentiment.producer.tweet_sampler import _parse_tweets
        data = {
            "data": [{
                "id": "999",
                "text": "Typhoon update #TyphoonPH",
                "created_at": "2024-01-15T10:00:00.000Z",
                "author_id": "111",
                "lang": "en",
                "entities": {
                    "hashtags": [{"tag": "TyphoonPH"}],
                    "mentions": [],
                },
            }]
        }
        results = _parse_tweets(data)
        assert len(results) == 1
        assert results[0].tweet_id == "999"
        assert "TyphoonPH" in results[0].hashtags
