"""
Simulator producer — replays pre-recorded JSON fixtures into Kafka.
Default mode: no API key, no live Twitter access needed.
Always demonstrable in a job interview.

Usage:
    python -m ph_sentiment.producer.simulator
    python -m ph_sentiment.producer.simulator --dry-run
"""

from __future__ import annotations

import json
import logging
import time
from datetime import datetime, timezone
from pathlib import Path
from typing import Optional

from ph_sentiment.config import settings
from ph_sentiment.models import TrendSnapshot, TweetEvent

logger = logging.getLogger(__name__)


def load_fixture(filename: str) -> dict | list:
    path = Path(settings.fixtures_dir) / filename
    if not path.exists():
        raise FileNotFoundError(f"Fixture not found: {path}")
    with open(path) as f:
        return json.load(f)


def parse_ww_trends(raw: list) -> list[TrendSnapshot]:
    """Parse WWTrends.json / USTrends.json into TrendSnapshot records."""
    records = []
    now = datetime.now(timezone.utc)
    for entry in raw:
        for trend in entry.get("trends", []):
            try:
                records.append(TrendSnapshot(
                    captured_at=now,
                    topic_name=trend.get("name", "unknown"),
                    tweet_volume=trend.get("tweet_volume"),
                    query=trend.get("query"),
                    region=entry.get("locations", [{}])[0].get("name", "WW"),
                    source="simulator",
                ))
            except Exception as e:
                logger.warning("Skipping trend record: %s", e)
    return records


def parse_tweets(raw: list) -> list[TweetEvent]:
    """Parse WeLoveTheEarth.json into TweetEvent records."""
    records = []
    for i, tweet in enumerate(raw):
        try:
            records.append(TweetEvent(
                tweet_id=str(tweet.get("id", f"sim_{i}")),
                created_at=datetime.now(timezone.utc),
                text=tweet.get("text", tweet.get("full_text", "")),
                author_id=str(tweet.get("user", {}).get("id", "")),
                lang=tweet.get("lang", "en"),
                source="simulator",
            ))
        except Exception as e:
            logger.warning("Skipping tweet record: %s", e)
    return records


def produce_to_kafka(
    trends: list[TrendSnapshot],
    tweets: list[TweetEvent],
    dry_run: bool = False,
) -> None:
    """Publish records to Kafka topics with configurable replay delay."""
    if dry_run:
        logger.info("[DRY RUN] Would produce %d trends + %d tweets to Kafka",
                    len(trends), len(tweets))
        for t in trends[:3]:
            logger.info("  TREND: %s (vol=%s)", t.topic_name, t.tweet_volume)
        for t in tweets[:3]:
            logger.info("  TWEET: %s...", t.text[:60])
        return

    try:
        from confluent_kafka import Producer
        producer = Producer({"bootstrap.servers": settings.kafka_bootstrap_servers})

        for trend in trends:
            producer.produce(
                settings.kafka_topic_trends,
                key=trend.topic_name.encode(),
                value=trend.model_dump_json().encode(),
            )
            time.sleep(settings.simulation_replay_delay_ms / 1000)

        for tweet in tweets:
            producer.produce(
                settings.kafka_topic_tweets,
                key=tweet.tweet_id.encode(),
                value=tweet.model_dump_json().encode(),
            )
            time.sleep(settings.simulation_replay_delay_ms / 1000)

        producer.flush()
        logger.info("Produced %d trends + %d tweets to Kafka.", len(trends), len(tweets))

    except ImportError:
        logger.error("confluent-kafka not installed. Install with: pip install confluent-kafka")
    except Exception as e:
        logger.error("Kafka produce failed: %s", e)


def run(dry_run: bool = False) -> tuple[int, int]:
    """
    Load all fixtures and produce to Kafka (or dry-run log).
    Returns (trend_count, tweet_count).
    """
    logging.basicConfig(level=logging.INFO, format="%(levelname)s %(message)s")

    trends: list[TrendSnapshot] = []
    tweets: list[TweetEvent] = []

    for fixture_file in ["WWTrends.json", "USTrends.json"]:
        try:
            raw = load_fixture(fixture_file)
            parsed = parse_ww_trends(raw if isinstance(raw, list) else [raw])
            trends.extend(parsed)
            logger.info("Loaded %d trends from %s", len(parsed), fixture_file)
        except FileNotFoundError:
            logger.warning("Fixture not found: %s — skipping", fixture_file)

    try:
        raw_tweets = load_fixture("WeLoveTheEarth.json")
        tweet_list = raw_tweets if isinstance(raw_tweets, list) else [raw_tweets]
        parsed_tweets = parse_tweets(tweet_list)
        tweets.extend(parsed_tweets)
        logger.info("Loaded %d tweets from WeLoveTheEarth.json", len(parsed_tweets))
    except FileNotFoundError:
        logger.warning("WeLoveTheEarth.json not found — skipping")

    produce_to_kafka(trends, tweets, dry_run=dry_run)
    return len(trends), len(tweets)


if __name__ == "__main__":
    import argparse
    parser = argparse.ArgumentParser()
    parser.add_argument("--dry-run", action="store_true")
    args = parser.parse_args()
    run(dry_run=args.dry_run)
