"""
Tweet sampler — keyword-filtered recent tweet stream via Twitter/X API v2.
Requires Basic tier. Falls back gracefully when unavailable.
"""

from __future__ import annotations

import logging
from datetime import datetime, timezone
from typing import Iterator

import requests

from ph_sentiment.config import settings
from ph_sentiment.models import TweetEvent

logger = logging.getLogger(__name__)

PH_KEYWORDS = [
    "Pilipinas", "Pilipino", "Maynila", "Mindanao", "Visayas", "Luzon",
    "#PHElections", "#PHWeather", "#TyphoonPH", "NDRRMC", "PAGASA",
]


def _headers() -> dict[str, str]:
    return {"Authorization": f"Bearer {settings.twitter_bearer_token}"}


def fetch_recent_tweets(
    keywords: list[str] | None = None,
    max_results: int = 100,
) -> list[TweetEvent]:
    """
    Fetch recent tweets matching PH keywords from Twitter API v2.
    Returns empty list when API is unavailable — use simulator.py instead.
    """
    if not settings.twitter_bearer_token:
        logger.warning("No Twitter bearer token configured.")
        return []

    query_terms = keywords or PH_KEYWORDS
    query = " OR ".join(query_terms[:5]) + " -is:retweet lang:tl OR lang:en"

    url = f"https://api.twitter.com/2/tweets/search/recent"
    params = {
        "query": query,
        "max_results": min(max_results, 100),
        "tweet.fields": "created_at,author_id,lang,entities",
    }

    try:
        resp = requests.get(url, headers=_headers(), params=params, timeout=30)
        if resp.status_code == 429:
            logger.warning("Rate limit hit on tweet sampler.")
            return []
        resp.raise_for_status()
        return _parse_tweets(resp.json())
    except requests.RequestException as e:
        logger.error("Tweet sampler request failed: %s", e)
        return []


def _parse_tweets(data: dict) -> list[TweetEvent]:
    records = []
    for tweet in data.get("data", []):
        entities = tweet.get("entities", {})
        hashtags = [h["tag"] for h in entities.get("hashtags", [])]
        mentions = [m["username"] for m in entities.get("mentions", [])]
        try:
            records.append(TweetEvent(
                tweet_id=tweet["id"],
                created_at=datetime.fromisoformat(
                    tweet.get("created_at", datetime.now(timezone.utc).isoformat())
                ),
                text=tweet.get("text", ""),
                author_id=tweet.get("author_id"),
                lang=tweet.get("lang"),
                hashtags=hashtags,
                mentions=mentions,
                source="twitter_v2",
            ))
        except Exception as e:
            logger.warning("Skipping tweet %s: %s", tweet.get("id"), e)
    return records
