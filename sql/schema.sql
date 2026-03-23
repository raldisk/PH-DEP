-- schema.sql
-- Raw schema DDL for ph-regional-inequality
-- Run once to create all tables before loading data

CREATE SCHEMA IF NOT EXISTS raw;

-- PSGC reference table — harmonizes provincial codes across all PSA datasets
CREATE TABLE IF NOT EXISTS raw.psgc_reference (
    psgc_code       CHAR(9)      PRIMARY KEY,
    region_code     CHAR(2)      NOT NULL,
    region_name     VARCHAR(100) NOT NULL,
    province_code   CHAR(5),
    province_name   VARCHAR(100),
    city_muni_code  CHAR(9),
    city_muni_name  VARCHAR(100),
    income_class    VARCHAR(20),
    population_2020 BIGINT,
    loaded_at       TIMESTAMPTZ  DEFAULT NOW()
);

-- FIES 2021 family income and expenditure
CREATE TABLE IF NOT EXISTS raw.fies_2021 (
    id                  SERIAL PRIMARY KEY,
    region_code         CHAR(2)       NOT NULL,
    region_name         VARCHAR(100)  NOT NULL,
    income_class        VARCHAR(50),
    total_income_php    NUMERIC(14,2),
    total_expenditure   NUMERIC(14,2),
    food_expenditure    NUMERIC(14,2),
    edu_expenditure     NUMERIC(14,2),
    health_expenditure  NUMERIC(14,2),
    housing_expenditure NUMERIC(14,2),
    per_capita_income   NUMERIC(14,2),
    household_size      NUMERIC(5,2),
    sample_weight       NUMERIC(10,4),
    loaded_at           TIMESTAMPTZ   DEFAULT NOW()
);

-- FIES 2023
CREATE TABLE IF NOT EXISTS raw.fies_2023 (
    LIKE raw.fies_2021 INCLUDING DEFAULTS EXCLUDING CONSTRAINTS
);
ALTER TABLE raw.fies_2023 ADD PRIMARY KEY (id);

-- Official poverty statistics — provincial level
CREATE TABLE IF NOT EXISTS raw.poverty_provincial (
    id                  SERIAL PRIMARY KEY,
    year                SMALLINT      NOT NULL,
    region_code         CHAR(2)       NOT NULL,
    region_name         VARCHAR(100)  NOT NULL,
    province_code       CHAR(5),
    province_name       VARCHAR(100),
    poverty_incidence   NUMERIC(6,2),  -- % of population below poverty threshold
    poverty_threshold   NUMERIC(12,2), -- PHP per year per person
    poverty_gap         NUMERIC(6,2),
    income_gap          NUMERIC(6,2),
    loaded_at           TIMESTAMPTZ   DEFAULT NOW(),
    UNIQUE (year, province_code)
);

-- Small Area Estimates — municipal level 2023
CREATE TABLE IF NOT EXISTS raw.poverty_sae_municipal (
    id                SERIAL PRIMARY KEY,
    psgc_code         CHAR(9)       NOT NULL,
    city_muni_name    VARCHAR(100)  NOT NULL,
    province_name     VARCHAR(100),
    region_name       VARCHAR(100)  NOT NULL,
    poverty_incidence NUMERIC(6,2)  NOT NULL,
    standard_error    NUMERIC(6,4),
    lower_ci_95       NUMERIC(6,2),
    upper_ci_95       NUMERIC(6,2),
    year              SMALLINT      DEFAULT 2023,
    loaded_at         TIMESTAMPTZ   DEFAULT NOW(),
    UNIQUE (psgc_code, year)
);

-- Census 2020 regional/provincial summary
CREATE TABLE IF NOT EXISTS raw.census_2020 (
    id              SERIAL PRIMARY KEY,
    psgc_code       CHAR(9),
    region_code     CHAR(2)      NOT NULL,
    region_name     VARCHAR(100) NOT NULL,
    province_code   CHAR(5),
    province_name   VARCHAR(100),
    population      BIGINT       NOT NULL,
    households      BIGINT,
    avg_hh_size     NUMERIC(4,2),
    pct_urban       NUMERIC(5,2),
    loaded_at       TIMESTAMPTZ  DEFAULT NOW()
);

-- Gross Regional Domestic Product
CREATE TABLE IF NOT EXISTS raw.grdp_regional (
    id             SERIAL PRIMARY KEY,
    year           SMALLINT     NOT NULL,
    region_code    CHAR(2)      NOT NULL,
    region_name    VARCHAR(100) NOT NULL,
    grdp_php_bn    NUMERIC(12,2),
    grdp_growth_pct NUMERIC(6,2),
    grdp_per_capita NUMERIC(12,2),
    loaded_at      TIMESTAMPTZ  DEFAULT NOW(),
    UNIQUE (year, region_code)
);

-- Indexes for common query patterns
CREATE INDEX IF NOT EXISTS idx_poverty_prov_year
    ON raw.poverty_provincial (year, region_code);

CREATE INDEX IF NOT EXISTS idx_fies_2023_region
    ON raw.fies_2023 (region_code);

CREATE INDEX IF NOT EXISTS idx_sae_region
    ON raw.poverty_sae_municipal (region_name);
