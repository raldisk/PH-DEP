"""Shared pytest fixtures for ph-regional-inequality tests."""

from __future__ import annotations

import pandas as pd
import pytest


@pytest.fixture
def sample_fies_row() -> dict:
    return {
        "region_code": "NCR",
        "region_name": "NCR",
        "total_income_php": 580000.0,
        "total_expenditure": 520000.0,
        "food_expenditure": 195000.0,
        "edu_expenditure": 42000.0,
        "health_expenditure": 28000.0,
        "housing_expenditure": 95000.0,
        "per_capita_income": 116000.0,
        "household_size": 5.0,
        "sample_weight": 1.2,
    }


@pytest.fixture
def sample_poverty_row() -> dict:
    return {
        "year": 2023,
        "region_code": "BARMM",
        "region_name": "BARMM",
        "province_code": None,
        "province_name": None,
        "poverty_incidence": 37.2,
        "poverty_threshold": 13500.0,
        "poverty_gap": 13.0,
        "income_gap": 16.7,
    }


@pytest.fixture
def sample_fies_df(sample_fies_row) -> pd.DataFrame:
    rows = []
    for region, income in [("NCR", 580000), ("BARMM", 160000), ("IVA", 450000)]:
        for i in range(50):
            row = sample_fies_row.copy()
            row["region_code"] = region
            row["region_name"] = region
            row["total_income_php"] = income * (0.8 + i * 0.008)
            rows.append(row)
    return pd.DataFrame(rows)


@pytest.fixture
def sample_poverty_df() -> pd.DataFrame:
    regions = [
        ("NCR", "NCR", 3.5, 4.1),
        ("BARMM", "BARMM", 37.2, 61.2),
        ("IVA", "CALABARZON", 8.7, 9.9),
    ]
    rows = []
    for code, name, pov_2023, pov_2021 in regions:
        for year, pov in [(2023, pov_2023), (2021, pov_2021)]:
            rows.append({
                "year": year, "region_code": code, "region_name": name,
                "province_code": None, "province_name": None,
                "poverty_incidence": pov,
            })
    return pd.DataFrame(rows)
