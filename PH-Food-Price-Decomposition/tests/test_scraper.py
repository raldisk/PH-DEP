"""Unit tests for scraper modules — data validation and sample generation."""

from __future__ import annotations

from pathlib import Path

import pandas as pd
import pytest


class TestScrapePSAPrices:
    def test_generate_sample_creates_csv(self, tmp_path, monkeypatch):
        import scripts.scrape_psa_prices as scraper
        monkeypatch.setattr(scraper, "DATA_DIR", tmp_path)
        monkeypatch.setattr(scraper, "PSA_DIR", tmp_path / "psa")
        (tmp_path / "psa").mkdir()
        scraper.generate_sample_data()
        assert (tmp_path / "psa_prices_sample.csv").exists()

    def test_sample_has_required_columns(self, tmp_path, monkeypatch):
        import scripts.scrape_psa_prices as scraper
        monkeypatch.setattr(scraper, "DATA_DIR", tmp_path)
        monkeypatch.setattr(scraper, "PSA_DIR", tmp_path / "psa")
        (tmp_path / "psa").mkdir()
        scraper.generate_sample_data()
        df = pd.read_csv(tmp_path / "psa_prices_sample.csv")
        required = ["price_date", "commodity_slug", "retail_price_php", "region", "phase"]
        for col in required:
            assert col in df.columns, f"Missing column: {col}"

    def test_prices_positive(self, tmp_path, monkeypatch):
        import scripts.scrape_psa_prices as scraper
        monkeypatch.setattr(scraper, "DATA_DIR", tmp_path)
        monkeypatch.setattr(scraper, "PSA_DIR", tmp_path / "psa")
        (tmp_path / "psa").mkdir()
        scraper.generate_sample_data()
        df = pd.read_csv(tmp_path / "psa_prices_sample.csv")
        assert (df["retail_price_php"] > 0).all()

    def test_onion_2023_spike(self, tmp_path, monkeypatch):
        """Onion prices in Jan 2023 should be significantly higher than 2022."""
        import scripts.scrape_psa_prices as scraper
        monkeypatch.setattr(scraper, "DATA_DIR", tmp_path)
        monkeypatch.setattr(scraper, "PSA_DIR", tmp_path / "psa")
        (tmp_path / "psa").mkdir()
        scraper.generate_sample_data()
        df = pd.read_csv(tmp_path / "psa_prices_sample.csv",
                         parse_dates=["price_date"])
        onion = df[df["commodity_slug"] == "onion_white"]
        avg_2022 = onion[onion["price_date"].dt.year == 2022]["retail_price_php"].mean()
        avg_2023 = onion[onion["price_date"].dt.year == 2023]["retail_price_php"].mean()
        assert avg_2023 > avg_2022 * 2, "2023 onion price should be 2x+ the 2022 average"

    def test_interpolate_price_returns_positive(self):
        import scripts.scrape_psa_prices as scraper
        for commodity in scraper.COMMODITIES:
            price = scraper.interpolate_price(commodity, 2024, 6)
            assert price > 0, f"{commodity} price should be positive"


class TestScrapeDOEFuel:
    def test_generate_sample_creates_csv(self, tmp_path, monkeypatch):
        import scripts.scrape_doe_fuel as scraper
        monkeypatch.setattr(scraper, "DATA_DIR", tmp_path)
        scraper.generate_sample_data()
        assert (tmp_path / "doe_fuel_prices.csv").exists()

    def test_sample_has_all_fuel_types(self, tmp_path, monkeypatch):
        import scripts.scrape_doe_fuel as scraper
        monkeypatch.setattr(scraper, "DATA_DIR", tmp_path)
        scraper.generate_sample_data()
        df = pd.read_csv(tmp_path / "doe_fuel_prices.csv")
        fuel_types = set(df["fuel_type"].unique())
        assert {"gasoline", "diesel", "lpg"} <= fuel_types

    def test_diesel_2022_spike(self, tmp_path, monkeypatch):
        """Diesel should spike in 2022 (Ukraine war)."""
        import scripts.scrape_doe_fuel as scraper
        monkeypatch.setattr(scraper, "DATA_DIR", tmp_path)
        scraper.generate_sample_data()
        df = pd.read_csv(tmp_path / "doe_fuel_prices.csv", parse_dates=["price_date"])
        diesel = df[df["fuel_type"] == "diesel"]
        avg_2019 = diesel[diesel["price_date"].dt.year == 2019]["price_php"].mean()
        avg_2022 = diesel[diesel["price_date"].dt.year == 2022]["price_php"].mean()
        assert avg_2022 > avg_2019 * 1.4, "2022 diesel should be significantly higher than 2019"
