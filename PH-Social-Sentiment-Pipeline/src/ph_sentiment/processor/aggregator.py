"""
5-minute windowed aggregation.
Groups tweet events by topic + 5-min window + sentiment label → counts.
Used for the trending_topics and sentiment_hourly mart inputs.
"""

from __future__ import annotations

from collections import defaultdict
from dataclasses import dataclass, field
from datetime import datetime, timedelta, timezone
from typing import Dict, List, Tuple

from ph_sentiment.models import TweetEvent


@dataclass
class WindowBucket:
    """Aggregated counts for one (window_start, topic_name) bucket."""
    window_start: datetime
    topic_name: str
    positive: int = 0
    neutral: int = 0
    negative: int = 0
    total: int = 0

    @property
    def sentiment_score(self) -> float:
        """Net sentiment: (positive - negative) / total."""
        if self.total == 0:
            return 0.0
        return round((self.positive - self.negative) / self.total, 4)

    @property
    def dominant_label(self) -> str:
        counts = {"positive": self.positive, "neutral": self.neutral, "negative": self.negative}
        return max(counts, key=counts.get)


def floor_to_window(dt: datetime, window_minutes: int = 5) -> datetime:
    """Round datetime down to nearest window boundary."""
    minutes = (dt.minute // window_minutes) * window_minutes
    return dt.replace(minute=minutes, second=0, microsecond=0)


def aggregate(
    tweets: List[TweetEvent],
    window_minutes: int = 5,
) -> List[WindowBucket]:
    """
    Aggregate tweet events into 5-minute sentiment windows per topic.
    Returns sorted list of WindowBucket objects.
    """
    buckets: Dict[Tuple[datetime, str], WindowBucket] = {}

    for tweet in tweets:
        if not tweet.topic_name or not tweet.sentiment_label:
            continue

        window_start = floor_to_window(tweet.created_at, window_minutes)
        key = (window_start, tweet.topic_name)

        if key not in buckets:
            buckets[key] = WindowBucket(
                window_start=window_start,
                topic_name=tweet.topic_name,
            )

        bucket = buckets[key]
        bucket.total += 1
        if tweet.sentiment_label == "positive":
            bucket.positive += 1
        elif tweet.sentiment_label == "negative":
            bucket.negative += 1
        else:
            bucket.neutral += 1

    return sorted(buckets.values(), key=lambda b: (b.window_start, b.topic_name))


def top_topics_by_volume(
    buckets: List[WindowBucket],
    top_n: int = 10,
) -> List[Tuple[str, int]]:
    """Return top N topics by total tweet volume across all windows."""
    topic_totals: Dict[str, int] = defaultdict(int)
    for b in buckets:
        topic_totals[b.topic_name] += b.total
    return sorted(topic_totals.items(), key=lambda x: x[1], reverse=True)[:top_n]
