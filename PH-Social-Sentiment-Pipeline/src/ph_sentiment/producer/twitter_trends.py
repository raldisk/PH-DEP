"""
Twitter/X API v2 live producer — trends poller.
Requires Basic tier ($100/month) — use simulator.py for demo/dev.

Gracefully falls back to simulator when:
  - No bearer token configured
  - API quota exhausted
  - Network unavailable
"""

from __future__ import annotations

import logging
import time
from datetime import datetime, timezone
from typing import Optional

import requests

from ph_sentiment.config import settings
from ph_sentiment.models import TrendSnapshot

logger = logging.getLogger(__name__)

TWITTER_API_BASE = "https://api.twitter.com/2"
PH_WOEID = 1199005  # Philippines WOEID for trending topics


def _headers() -> dict[str, str]:
    return {"Authorization": f"Bearer {settings.twitter_bearer_token}"}


def fetch_trending_topics(woeid: int = PH_WOEID) -> list[TrendSnapshot]:
    """
    Fetch currently trending topics for a given WOEID from Twitter/X API v2.
    Returns empty list if API unavailable or quota exceeded.
    Note: Twitter v1.1 trends endpoint (trends/place) is not available on
    Basic tier. This uses v2 search/recent as a proxy for trending signals.
    """
    if not settings.twitter_bearer_token:
        logger.warning("No Twitter bearer token — use simulation mode instead.")
        return []

    # v2 recent search for PH-language tweets (proxy for trending)
    url = f"{TWITTER_API_BASE}/tweets/search/recent"
    params = {
        "query": "lang:tl OR (lang:en place_country:PH) -is:retweet",
        "max_results": 100,
        "tweet.fields": "lang,created_at,author_id,entities",
    }

    try:
        resp = requests.get(url, headers=_headers(), params=params, timeout=30)
        if resp.status_code == 429:
            logger.warning("Twitter API rate limit hit — sleeping 15 minutes.")
            time.sleep(900)
            return []
        resp.raise_for_status()
        data = resp.json()
        return _parse_v2_response(data)
    except requests.RequestException as e:
        logger.error("Twitter API request failed: %s", e)
        return []


def _parse_v2_response(data: dict) -> list[TrendSnapshot]:
    records = []
    now = datetime.now(timezone.utc)
    for tweet in data.get("data", []):
        hashtags = [
            tag["tag"] for tag in
            tweet.get("entities", {}).get("hashtags", [])
        ]
        for tag in hashtags:
            records.append(TrendSnapshot(
                captured_at=now,
                topic_name=f"#{tag}",
                tweet_volume=None,
                region="PH",
                source="twitter_v2",
            ))
    return records
