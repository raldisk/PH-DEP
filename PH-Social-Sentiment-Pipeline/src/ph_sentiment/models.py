"""
Pydantic v2 domain models.
Every record from every source is validated here before hitting Kafka or PostgreSQL.
"""

from __future__ import annotations

from datetime import datetime
from typing import Optional

from pydantic import BaseModel, Field, field_validator


class TrendSnapshot(BaseModel):
    """A single trending topic observation."""

    captured_at: datetime
    topic_name: str = Field(..., min_length=1, max_length=280)
    tweet_volume: Optional[int] = None
    query: Optional[str] = None
    region: str = "PH"
    source: str = "simulator"   # 'simulator' | 'twitter_v2'

    @field_validator("topic_name")
    @classmethod
    def strip_topic(cls, v: str) -> str:
        return v.strip()

    @field_validator("tweet_volume")
    @classmethod
    def non_negative_volume(cls, v: Optional[int]) -> Optional[int]:
        if v is not None and v < 0:
            return None
        return v


class TweetEvent(BaseModel):
    """A single tweet event."""

    tweet_id: str
    created_at: datetime
    text: str = Field(..., min_length=1, max_length=560)
    author_id: Optional[str] = None
    lang: Optional[str] = None
    hashtags: list[str] = Field(default_factory=list)
    mentions: list[str] = Field(default_factory=list)
    source: str = "simulator"

    # Enrichment fields (filled by processor)
    sentiment_label: Optional[str] = None    # positive | neutral | negative
    sentiment_score: Optional[float] = None  # -1.0 to 1.0
    topic_name: Optional[str] = None

    @field_validator("text")
    @classmethod
    def strip_text(cls, v: str) -> str:
        return v.strip()

    @field_validator("sentiment_label")
    @classmethod
    def valid_label(cls, v: Optional[str]) -> Optional[str]:
        if v is not None and v not in ("positive", "neutral", "negative"):
            raise ValueError(f"Invalid sentiment label: {v}")
        return v
