"""
End-to-end simulation runner — no API key, no live Kafka required.
Loads fixtures → enriches + classifies → writes directly to PostgreSQL.

Usage:
    python scripts/run_simulation.py            # full run
    python scripts/run_simulation.py --dry-run  # log only, no DB writes
"""

from __future__ import annotations

import argparse
import logging
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent / "src"))

logging.basicConfig(level=logging.INFO, format="%(levelname)s %(message)s")
logger = logging.getLogger(__name__)


def main(dry_run: bool = False) -> None:
    from ph_sentiment.loader import ensure_schema, upsert_trends, upsert_tweets, row_counts
    from ph_sentiment.processor.enrichment import enrich_batch
    from ph_sentiment.processor.sentiment import classify_batch
    from ph_sentiment.producer.simulator import run as sim_run, parse_ww_trends, parse_tweets, load_fixture

    logger.info("=" * 55)
    logger.info("PH Social Sentiment Pipeline — Simulation Mode")
    logger.info("=" * 55)

    # Step 1 — Load fixtures
    trends, tweets = [], []

    for fname in ["WWTrends.json", "USTrends.json"]:
        try:
            raw = load_fixture(fname)
            parsed = parse_ww_trends(raw if isinstance(raw, list) else [raw])
            trends.extend(parsed)
            logger.info("Loaded %d trends from %s", len(parsed), fname)
        except FileNotFoundError:
            logger.warning("Fixture missing: %s — skipping", fname)

    try:
        raw_tweets = load_fixture("WeLoveTheEarth.json")
        tweet_list = raw_tweets if isinstance(raw_tweets, list) else [raw_tweets]
        parsed_tweets = parse_tweets(tweet_list)
        tweets.extend(parsed_tweets)
        logger.info("Loaded %d tweets from WeLoveTheEarth.json", len(parsed_tweets))
    except FileNotFoundError:
        logger.warning("WeLoveTheEarth.json not found — skipping")

    if not trends and not tweets:
        logger.error("No fixture data found. Check fixtures/ directory.")
        sys.exit(1)

    # Step 2 — Enrich tweets (hashtags, mentions)
    tweets = enrich_batch(tweets)
    logger.info("Enrichment complete — %d tweets processed", len(tweets))

    # Step 3 — Sentiment classification
    # Assign topic_name from first available trend
    if trends and tweets:
        topic_sample = [t.topic_name for t in trends[:5]]
        for i, tweet in enumerate(tweets):
            tweet.topic_name = topic_sample[i % len(topic_sample)]

    tweets = classify_batch(tweets)
    classified = sum(1 for t in tweets if t.sentiment_label is not None)
    logger.info("Sentiment classification complete — %d/%d classified", classified, len(tweets))

    # Step 4 — Show sample results
    logger.info("\n--- Sample classifications ---")
    for t in tweets[:5]:
        logger.info("  [%s %.2f] %s...",
                    t.sentiment_label or "?",
                    t.sentiment_score or 0.0,
                    t.text[:70])

    if dry_run:
        logger.info("\n[DRY RUN] Would write %d trends + %d tweets to PostgreSQL", len(trends), len(tweets))
        logger.info("Pass without --dry-run to write to the database.")
        return

    # Step 5 — Write to PostgreSQL
    logger.info("\nWriting to PostgreSQL...")
    ensure_schema()
    t_count = upsert_trends(trends)
    tw_count = upsert_tweets(tweets)
    logger.info("Written: %d trends + %d tweets", t_count, tw_count)

    # Step 6 — Show row counts
    counts = row_counts()
    logger.info("\n--- Warehouse row counts ---")
    for table, count in counts.items():
        logger.info("  %s: %d rows", table, count)

    logger.info("\nSimulation complete. Open Streamlit dashboard to explore results.")
    logger.info("  streamlit run dashboard/app.py")


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="PH Sentiment simulation runner")
    parser.add_argument("--dry-run", action="store_true",
                        help="Log only — no database writes")
    args = parser.parse_args()
    main(dry_run=args.dry_run)
