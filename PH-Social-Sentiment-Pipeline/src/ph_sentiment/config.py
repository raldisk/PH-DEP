"""
Configuration — all values driven by environment variables via pydantic-settings.
Copy .env.example → .env before running.
"""

from __future__ import annotations

from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(
        env_prefix="PH_SENTIMENT_",
        env_file=".env",
        env_file_encoding="utf-8",
        case_sensitive=False,
    )

    # Pipeline mode: 'simulate' (default, no API key) or 'live'
    mode: str = "simulate"

    # PostgreSQL
    postgres_dsn: str = "postgresql://sentiment:sentiment@localhost:5432/ph_sentiment"
    pg_host: str = "postgres"
    pg_port: int = 5432
    pg_user: str = "sentiment"
    pg_password: str = "sentiment"
    pg_dbname: str = "ph_sentiment"

    # Kafka
    kafka_bootstrap_servers: str = "localhost:9092"
    kafka_topic_trends: str = "ph.trends.raw"
    kafka_topic_tweets: str = "ph.tweets.raw"
    kafka_group_id: str = "ph-sentiment-consumer"

    # Sentiment model
    sentiment_model: str = "cardiffnlp/twitter-xlm-roberta-base-sentiment"
    sentiment_batch_size: int = 32
    use_vader_fallback: bool = True   # VADER as fast fallback on CPU-only

    # Twitter/X API (only needed in live mode)
    twitter_bearer_token: str = ""
    twitter_ph_woeid: int = 1199005   # Philippines WOEID

    # Simulation
    simulation_replay_delay_ms: int = 100   # ms between replayed messages
    fixtures_dir: str = "fixtures"


settings = Settings()
