"""
Pipeline CLI entry point.

Commands:
  ph-sentiment ingest     — run simulator or live ingest → PostgreSQL → dbt
  ph-sentiment transform  — run dbt models only
  ph-sentiment status     — print row counts + latest data
  ph-sentiment reset      — drop raw schema (destructive)

Usage:
  # Simulation mode (default, no API key needed)
  ph-sentiment ingest

  # Live mode (requires Twitter/X Basic tier)
  PH_SENTIMENT_MODE=live ph-sentiment ingest

  # Or via Docker
  docker compose run --rm simulator
"""

from __future__ import annotations

import logging
import subprocess
import sys
from pathlib import Path

import typer
from rich.console import Console
from rich.table import Table

from ph_sentiment.config import settings
from ph_sentiment.loader import ensure_schema, row_counts, upsert_trends, upsert_tweets
from ph_sentiment.processor.enrichment import enrich_batch
from ph_sentiment.processor.sentiment import classify_batch

app     = typer.Typer(name="ph-sentiment", help="PH Social Sentiment Pipeline", no_args_is_help=True)
console = Console()
logger  = logging.getLogger(__name__)

DBT_DIR = Path(__file__).parent.parent.parent / "transforms"


@app.command()
def ingest(
    dry_run:  bool = typer.Option(False, "--dry-run",   help="Log only — no DB or Kafka writes"),
    skip_dbt: bool = typer.Option(False, "--skip-dbt",  help="Skip dbt transforms after ingest"),
) -> None:
    """
    Ingest trends and tweets → enrich → classify sentiment → PostgreSQL → dbt.
    Runs in simulation mode by default (fixture replay, no API key needed).
    Set PH_SENTIMENT_MODE=live to use Twitter/X API v2.
    """
    logging.basicConfig(level=logging.INFO, format="%(levelname)s %(message)s")
    mode = settings.mode

    console.print(f"[bold blue]Mode: {mode.upper()}[/bold blue]")

    if not dry_run:
        ensure_schema()

    trends = []
    tweets = []

    if mode == "simulate":
        from ph_sentiment.producer.simulator import run as sim_run
        n_trends, n_tweets = sim_run(dry_run=dry_run)
        console.print(f"  Simulator: {n_trends} trends + {n_tweets} tweets produced")
        if dry_run:
            raise typer.Exit()

        # Re-parse fixtures for enrichment + sentiment
        from ph_sentiment.producer.simulator import (
            load_fixture, parse_tweets, parse_ww_trends,
        )
        for fixture in ["WWTrends.json", "USTrends.json"]:
            try:
                raw = load_fixture(fixture)
                trends.extend(parse_ww_trends(raw if isinstance(raw, list) else [raw]))
            except FileNotFoundError:
                pass
        try:
            raw_tweets = load_fixture("WeLoveTheEarth.json")
            tweet_list = raw_tweets if isinstance(raw_tweets, list) else [raw_tweets]
            tweets.extend(parse_tweets(tweet_list))
        except FileNotFoundError:
            pass

    elif mode == "live":
        from ph_sentiment.producer.twitter_trends import fetch_trending_topics
        from ph_sentiment.producer.tweet_sampler import fetch_recent_tweets
        trends = fetch_trending_topics()
        tweets = fetch_recent_tweets()
        console.print(f"  Live API: {len(trends)} trends + {len(tweets)} tweets fetched")

    else:
        console.print(f"[red]Unknown mode: {mode}. Use 'simulate' or 'live'.[/red]")
        raise typer.Exit(1)

    # Enrich + classify
    console.print("[bold blue]Enriching and classifying...[/bold blue]")
    tweets = enrich_batch(tweets)
    tweets = classify_batch(tweets)

    # Persist
    n_trends  = upsert_trends(trends)
    n_tweets  = upsert_tweets(tweets)
    console.print(f"\n[bold green]Ingest complete — {n_trends} trends + {n_tweets} tweets persisted.[/bold green]")

    if not skip_dbt:
        transform()


@app.command()
def transform(
    target: str = typer.Option("dev", help="dbt target profile"),
) -> None:
    """Run dbt models to rebuild mart tables from raw data."""
    console.print("[bold blue]Running dbt...[/bold blue]")
    result = subprocess.run(
        [sys.executable, "-m", "dbt", "run",
         "--profiles-dir", str(DBT_DIR), "--target", target],
        cwd=DBT_DIR,
    )
    if result.returncode != 0:
        console.print("[bold red]dbt run failed.[/bold red]")
        raise typer.Exit(1)
    console.print("[bold green]dbt complete.[/bold green]")


@app.command()
def status() -> None:
    """Show row counts for all raw tables."""
    counts = row_counts()
    t = Table(title="ph-sentiment — Warehouse Status")
    t.add_column("Table",  style="cyan")
    t.add_column("Rows",   justify="right", style="green")
    for table, count in counts.items():
        t.add_row(table, f"{count:,}")
    console.print(t)


@app.command()
def reset(
    confirm: bool = typer.Option(False, "--confirm", help="Required — drops raw schema"),
) -> None:
    """Drop raw schema (destructive). Requires --confirm."""
    if not confirm:
        console.print("[red]Pass --confirm to proceed.[/red]")
        raise typer.Exit(1)
    import psycopg2
    from ph_sentiment.loader import get_connection
    with get_connection() as conn:
        with conn.cursor() as cur:
            cur.execute("DROP SCHEMA IF EXISTS raw CASCADE;")
        conn.commit()
    console.print("[bold red]Raw schema dropped.[/bold red]")


if __name__ == "__main__":
    app()
