"""Shared pytest fixtures for ph-social-sentiment-pipeline."""

from __future__ import annotations

from datetime import datetime, timezone

import pytest

from ph_sentiment.models import TrendSnapshot, TweetEvent


@pytest.fixture
def sample_trend():
    return TrendSnapshot(
        captured_at=datetime(2024, 6, 1, 10, 0, tzinfo=timezone.utc),
        topic_name="#WeLoveTheEarth",
        tweet_volume=123456,
        query="%23WeLoveTheEarth",
        region="WW",
        source="simulator",
    )


@pytest.fixture
def sample_tweet():
    return TweetEvent(
        tweet_id="1001",
        created_at=datetime(2024, 6, 1, 10, 0, tzinfo=timezone.utc),
        text="I love this planet! #WeLoveTheEarth #EarthDay",
        author_id="u001",
        lang="en",
        source="simulator",
    )


@pytest.fixture
def sample_tweets():
    return [
        TweetEvent(
            tweet_id=str(i),
            created_at=datetime(2024, 6, 1, 10, 0, tzinfo=timezone.utc),
            text=text,
            lang=lang,
            source="simulator",
        )
        for i, (text, lang) in enumerate([
            ("I love the Earth! #WeLoveTheEarth", "en"),
            ("Mahal ko ang ating kalikasan!", "tl"),
            ("Disappointed by climate inaction. #ClimateAction", "en"),
            ("Neutral observation about weather today.", "en"),
            ("Grabe yung init! #SaveThePlanet", "tl"),
        ])
    ]


@pytest.fixture
def ww_trends_fixture():
    return [{
        "trends": [
            {"name": "#WeLoveTheEarth", "query": "%23WeLoveTheEarth", "tweet_volume": 100000},
            {"name": "#EarthDay", "query": "%23EarthDay", "tweet_volume": 50000},
        ],
        "locations": [{"name": "Worldwide", "woeid": 1}],
    }]
