"""Shared pytest fixtures for ph-food-price-decomposition tests."""

from __future__ import annotations

from datetime import date

import pandas as pd
import pytest


@pytest.fixture
def sample_psa_row() -> dict:
    return {
        "price_date": date(2024, 1, 15),
        "phase": 1,
        "commodity": "Well-milled rice",
        "commodity_slug": "rice_wellmilled",
        "retail_price_php": 53.54,
        "unit": "kg",
        "region": "National",
        "source": "psa_situationer",
    }


@pytest.fixture
def sample_psa_df() -> pd.DataFrame:
    dates = pd.date_range("2020-01-01", "2024-12-31", freq="MS")
    rows = []
    for dt in dates:
        for commodity, base_price in [
            ("rice_wellmilled", 45.0),
            ("onion_white", 65.0),
            ("tomato", 60.0),
        ]:
            for phase in [1, 2]:
                rows.append({
                    "price_date": dt.date(),
                    "phase": phase,
                    "commodity": commodity.replace("_", " ").title(),
                    "commodity_slug": commodity,
                    "retail_price_php": round(base_price + (dt.year - 2020) * 2.5 + phase * 0.5, 2),
                    "unit": "kg",
                    "region": "National",
                    "source": "test",
                })
    return pd.DataFrame(rows)


@pytest.fixture
def sample_fuel_df() -> pd.DataFrame:
    dates = pd.date_range("2015-01-01", "2024-12-31", freq="W-MON")
    rows = []
    for dt in dates:
        for fuel, base in [("diesel", 45.0), ("gasoline", 55.0)]:
            rows.append({
                "price_date": dt.date(),
                "fuel_type": fuel,
                "price_php": round(base + (dt.year - 2015) * 2.0, 2),
                "region": "National",
                "source": "doe_test",
            })
    return pd.DataFrame(rows)
