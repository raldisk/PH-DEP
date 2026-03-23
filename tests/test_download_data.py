"""Unit tests for download_data.py — schema validation and sample generation."""

from __future__ import annotations

from pathlib import Path
import pandas as pd
import pytest


class TestValidateSchema:
    def test_valid_csv(self, tmp_path):
        from scripts.download_data import validate_schema
        csv = tmp_path / "test.csv"
        pd.DataFrame({"date": ["2024-01"], "price": [55.0], "market": ["Manila"]}).to_csv(csv, index=False)
        assert validate_schema(csv, ["date", "price", "market"]) is True

    def test_missing_columns(self, tmp_path):
        from scripts.download_data import validate_schema
        csv = tmp_path / "test.csv"
        pd.DataFrame({"date": ["2024-01"]}).to_csv(csv, index=False)
        assert validate_schema(csv, ["date", "price"]) is False

    def test_nonexistent_file(self, tmp_path):
        from scripts.download_data import validate_schema
        assert validate_schema(tmp_path / "missing.csv", ["col"]) is False


class TestGenerateSampleData:
    def test_generates_all_files(self, tmp_path, monkeypatch):
        import scripts.download_data as dd
        monkeypatch.setattr(dd, "DATA_DIR", tmp_path)

        dd.generate_sample_data()

        expected = [
            "fies_2023.csv", "fies_2021.csv",
            "poverty_provincial_2023.csv",
            "poverty_sae_municipal_2023.csv",
            "census_2020_regional.csv",
            "grdp_regional.csv",
        ]
        for fname in expected:
            assert (tmp_path / fname).exists(), f"Missing: {fname}"

    def test_fies_has_required_columns(self, tmp_path, monkeypatch):
        import scripts.download_data as dd
        monkeypatch.setattr(dd, "DATA_DIR", tmp_path)
        dd.generate_sample_data()

        df = pd.read_csv(tmp_path / "fies_2023.csv")
        required = ["region_code", "region_name", "total_income_php",
                    "total_expenditure", "food_expenditure", "household_size"]
        for col in required:
            assert col in df.columns, f"Missing column: {col}"

    def test_poverty_has_17_regions(self, tmp_path, monkeypatch):
        import scripts.download_data as dd
        monkeypatch.setattr(dd, "DATA_DIR", tmp_path)
        dd.generate_sample_data()

        df = pd.read_csv(tmp_path / "poverty_provincial_2023.csv")
        regions = df["region_code"].nunique()
        assert regions == 17

    def test_sae_has_positive_poverty_values(self, tmp_path, monkeypatch):
        import scripts.download_data as dd
        monkeypatch.setattr(dd, "DATA_DIR", tmp_path)
        dd.generate_sample_data()

        df = pd.read_csv(tmp_path / "poverty_sae_municipal_2023.csv")
        assert (df["poverty_incidence"] > 0).all()
        assert (df["poverty_incidence"] <= 100).all()
