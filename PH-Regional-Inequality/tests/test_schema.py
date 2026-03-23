"""Unit tests for data schema consistency."""

from __future__ import annotations

import pandas as pd
import pytest


class TestFIESSchema:
    def test_income_positive(self, sample_fies_df):
        assert (sample_fies_df["total_income_php"] > 0).all()

    def test_household_size_reasonable(self, sample_fies_df):
        assert (sample_fies_df["household_size"] > 0).all()
        assert (sample_fies_df["household_size"] < 20).all()

    def test_expenditure_less_than_income(self, sample_fies_df):
        # Most households spend less than they earn
        ratio = (sample_fies_df["total_expenditure"] < sample_fies_df["total_income_php"]).mean()
        assert ratio > 0.5  # majority should have savings


class TestPovertySchema:
    def test_incidence_range(self, sample_poverty_df):
        pov = sample_poverty_df["poverty_incidence"]
        assert (pov >= 0).all()
        assert (pov <= 100).all()

    def test_ncr_lowest_poverty(self, sample_poverty_df):
        pov_2023 = sample_poverty_df[sample_poverty_df["year"] == 2023].set_index("region_name")
        assert pov_2023.loc["NCR", "poverty_incidence"] < pov_2023.loc["BARMM", "poverty_incidence"]

    def test_barmm_improved_2021_to_2023(self, sample_poverty_df):
        barmm = sample_poverty_df[sample_poverty_df["region_name"] == "BARMM"]
        pov_2021 = barmm[barmm["year"] == 2021]["poverty_incidence"].values[0]
        pov_2023 = barmm[barmm["year"] == 2023]["poverty_incidence"].values[0]
        assert pov_2023 < pov_2021, "BARMM should show improvement 2021→2023"

    def test_years_present(self, sample_poverty_df):
        years = set(sample_poverty_df["year"].unique())
        assert 2021 in years
        assert 2023 in years


class TestPSGCCodes:
    def test_region_codes_format(self, sample_poverty_df):
        """Region codes should be non-empty strings."""
        codes = sample_poverty_df["region_code"].dropna()
        assert (codes.str.len() > 0).all()

    def test_no_duplicate_region_year(self, sample_poverty_df):
        """Each region should appear once per year at regional level."""
        regional = sample_poverty_df[sample_poverty_df["province_code"].isna()]
        dupes = regional.duplicated(subset=["region_code", "year"])
        assert not dupes.any(), "Duplicate region+year combinations found"
