-- schema.sql
-- Raw schema DDL for ph-food-price-decomposition
-- Run once before loading data

CREATE SCHEMA IF NOT EXISTS raw;

-- PSA Price Situationer — bi-phase commodity prices
CREATE TABLE IF NOT EXISTS raw.psa_price_situationer (
    id                BIGSERIAL     PRIMARY KEY,
    price_date        DATE          NOT NULL,
    phase             SMALLINT      NOT NULL DEFAULT 1,  -- 1 = first half, 2 = second half
    commodity         VARCHAR(100)  NOT NULL,
    commodity_slug    VARCHAR(50)   NOT NULL,            -- normalized: rice_wellmilled, onion, etc.
    retail_price_php  NUMERIC(10,2) NOT NULL,
    unit              VARCHAR(20)   DEFAULT 'kg',
    region            VARCHAR(50)   DEFAULT 'National',
    source            VARCHAR(50)   DEFAULT 'psa_situationer',
    scrape_date       DATE          DEFAULT CURRENT_DATE,
    loaded_at         TIMESTAMPTZ   DEFAULT NOW(),
    UNIQUE (price_date, phase, commodity_slug, region)
);

-- Monthly CPI by commodity group (PSA OpenSTAT)
CREATE TABLE IF NOT EXISTS raw.cpi_monthly (
    id              BIGSERIAL     PRIMARY KEY,
    period_date     DATE          NOT NULL,
    commodity_group VARCHAR(100)  NOT NULL,  -- 'Food', 'Rice', 'Vegetables', etc.
    cpi_index       NUMERIC(10,4) NOT NULL,
    inflation_pct   NUMERIC(8,4),
    base_year       SMALLINT      DEFAULT 2018,
    source          VARCHAR(50)   DEFAULT 'psa_openstat',
    loaded_at       TIMESTAMPTZ   DEFAULT NOW(),
    UNIQUE (period_date, commodity_group)
);

-- WFP food prices Philippines (HDX)
CREATE TABLE IF NOT EXISTS raw.wfp_food_prices (
    id                BIGSERIAL     PRIMARY KEY,
    price_date        DATE          NOT NULL,
    admin1            VARCHAR(100),           -- region/province
    market            VARCHAR(100),
    commodity         VARCHAR(100)  NOT NULL,
    unit              VARCHAR(20),
    price_php         NUMERIC(10,2),
    price_usd         NUMERIC(10,4),
    source            VARCHAR(50)   DEFAULT 'wfp_hdx',
    loaded_at         TIMESTAMPTZ   DEFAULT NOW(),
    UNIQUE (price_date, market, commodity)
);

-- DOE weekly fuel prices
CREATE TABLE IF NOT EXISTS raw.doe_fuel_prices (
    id             BIGSERIAL     PRIMARY KEY,
    price_date     DATE          NOT NULL,
    fuel_type      VARCHAR(50)   NOT NULL,   -- 'gasoline', 'diesel', 'lpg'
    price_php      NUMERIC(10,2) NOT NULL,
    region         VARCHAR(50)   DEFAULT 'National',
    source         VARCHAR(50)   DEFAULT 'doe_oil_monitor',
    loaded_at      TIMESTAMPTZ   DEFAULT NOW(),
    UNIQUE (price_date, fuel_type, region)
);

-- World Bank Pink Sheet — global commodity prices
CREATE TABLE IF NOT EXISTS raw.worldbank_pinksheet (
    id             BIGSERIAL     PRIMARY KEY,
    period_date    DATE          NOT NULL,
    commodity      VARCHAR(100)  NOT NULL,   -- 'crude_oil', 'rice_thai', 'wheat', etc.
    price_usd      NUMERIC(12,4) NOT NULL,
    unit           VARCHAR(30),
    source         VARCHAR(50)   DEFAULT 'wb_pinksheet',
    loaded_at      TIMESTAMPTZ   DEFAULT NOW(),
    UNIQUE (period_date, commodity)
);

-- Indexes
CREATE INDEX IF NOT EXISTS idx_psa_commodity_date
    ON raw.psa_price_situationer (commodity_slug, price_date);

CREATE INDEX IF NOT EXISTS idx_cpi_date
    ON raw.cpi_monthly (period_date, commodity_group);

CREATE INDEX IF NOT EXISTS idx_doe_date
    ON raw.doe_fuel_prices (price_date, fuel_type);

CREATE INDEX IF NOT EXISTS idx_wb_date
    ON raw.worldbank_pinksheet (period_date, commodity);
