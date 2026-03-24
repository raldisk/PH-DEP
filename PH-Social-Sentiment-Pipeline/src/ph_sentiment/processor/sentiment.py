"""
Sentiment classifier.
Primary: cardiffnlp/twitter-xlm-roberta-base-sentiment (handles Taglish)
Fallback: VADER (English-only, CPU-fast, no GPU needed)

Batch inference on windows of tweets — not per-message to avoid latency spikes.
"""

from __future__ import annotations

import logging
from typing import Optional

from ph_sentiment.config import settings
from ph_sentiment.models import TweetEvent

logger = logging.getLogger(__name__)

# Label map from XLM-RoBERTa model output
LABEL_MAP = {
    "LABEL_0": "negative",
    "LABEL_1": "neutral",
    "LABEL_2": "positive",
    # Model may also return these directly
    "negative": "negative",
    "neutral": "neutral",
    "positive": "positive",
}

SCORE_MAP = {"positive": 1.0, "neutral": 0.0, "negative": -1.0}

_pipeline = None
_vader = None


def _get_pipeline():
    global _pipeline
    if _pipeline is None:
        try:
            from transformers import pipeline as hf_pipeline
            _pipeline = hf_pipeline(
                "sentiment-analysis",
                model=settings.sentiment_model,
                tokenizer=settings.sentiment_model,
                truncation=True,
                max_length=128,
            )
            logger.info("Loaded HuggingFace model: %s", settings.sentiment_model)
        except Exception as e:
            logger.warning("Could not load HuggingFace model (%s) — VADER fallback active.", e)
    return _pipeline


def _get_vader():
    global _vader
    if _vader is None and settings.use_vader_fallback:
        try:
            from vaderSentiment.vaderSentiment import SentimentIntensityAnalyzer
            _vader = SentimentIntensityAnalyzer()
            logger.info("VADER sentiment analyzer loaded.")
        except ImportError:
            logger.warning("vaderSentiment not installed — no fallback available.")
    return _vader


def _classify_vader(text: str) -> tuple[str, float]:
    vader = _get_vader()
    if vader is None:
        return "neutral", 0.0
    scores = vader.polarity_scores(text)
    compound = scores["compound"]
    if compound >= 0.05:
        return "positive", compound
    elif compound <= -0.05:
        return "negative", compound
    return "neutral", compound


def classify_batch(tweets: list[TweetEvent]) -> list[TweetEvent]:
    """
    Classify sentiment for a batch of TweetEvent records.
    Modifies in-place and returns the list.
    """
    if not tweets:
        return tweets

    texts = [t.text for t in tweets]
    pipe = _get_pipeline()

    if pipe is not None:
        try:
            results = pipe(texts, batch_size=settings.sentiment_batch_size)
            for tweet, result in zip(tweets, results):
                label = LABEL_MAP.get(result["label"], "neutral")
                tweet.sentiment_label = label
                tweet.sentiment_score = round(
                    result["score"] * SCORE_MAP.get(label, 0.0), 4
                )
            return tweets
        except Exception as e:
            logger.warning("HuggingFace batch failed (%s) — falling back to VADER.", e)

    # VADER fallback — per-tweet
    for tweet in tweets:
        label, score = _classify_vader(tweet.text)
        tweet.sentiment_label = label
        tweet.sentiment_score = round(score, 4)

    return tweets


def classify_single(text: str) -> tuple[str, float]:
    """Classify a single text string. Returns (label, score)."""
    pipe = _get_pipeline()
    if pipe is not None:
        try:
            result = pipe([text])[0]
            label = LABEL_MAP.get(result["label"], "neutral")
            score = round(result["score"] * SCORE_MAP.get(label, 0.0), 4)
            return label, score
        except Exception:
            pass
    return _classify_vader(text)
