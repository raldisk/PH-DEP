"""
Enrichment processor — extracts hashtags, mentions from tweet text.
Also normalizes timestamps to Asia/Manila timezone.
"""

from __future__ import annotations

import re
from datetime import datetime, timezone

from ph_sentiment.models import TweetEvent

HASHTAG_RE = re.compile(r"#(\w+)", re.UNICODE)
MENTION_RE  = re.compile(r"@(\w+)", re.UNICODE)
MANILA_TZ_OFFSET = 8  # UTC+8


def enrich_tweet(tweet: TweetEvent) -> TweetEvent:
    """
    Extract hashtags + mentions from tweet text if not already populated.
    Normalizes created_at to UTC (stored as UTC, displayed as Manila time in dashboard).
    """
    if not tweet.hashtags:
        tweet.hashtags = HASHTAG_RE.findall(tweet.text)

    if not tweet.mentions:
        tweet.mentions = MENTION_RE.findall(tweet.text)

    # Ensure timezone-aware datetime
    if tweet.created_at.tzinfo is None:
        tweet.created_at = tweet.created_at.replace(tzinfo=timezone.utc)

    return tweet


def enrich_batch(tweets: list[TweetEvent]) -> list[TweetEvent]:
    return [enrich_tweet(t) for t in tweets]


def extract_top_hashtags(tweets: list[TweetEvent], top_n: int = 20) -> list[tuple[str, int]]:
    """Count hashtag frequency across a list of tweets."""
    from collections import Counter
    all_tags = [tag.lower() for t in tweets for tag in t.hashtags]
    return Counter(all_tags).most_common(top_n)


def extract_top_mentions(tweets: list[TweetEvent], top_n: int = 20) -> list[tuple[str, int]]:
    """Count mention frequency across a list of tweets."""
    from collections import Counter
    all_mentions = [m.lower() for t in tweets for m in t.mentions]
    return Counter(all_mentions).most_common(top_n)
