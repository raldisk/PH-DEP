-- fies_income_deciles.sql
-- Income decile shares by region — 2023 FIES
-- Reveals within-region inequality beyond the national Gini

WITH ranked AS (
    SELECT
        region_code,
        region_name,
        total_income_php,
        sample_weight,
        NTILE(10) OVER (
            PARTITION BY region_code
            ORDER BY total_income_php
        ) AS decile
    FROM raw.fies_2023
    WHERE total_income_php IS NOT NULL
      AND total_income_php > 0
),

weighted AS (
    SELECT
        region_code,
        region_name,
        decile,
        SUM(total_income_php * sample_weight)               AS decile_income_wt,
        SUM(SUM(total_income_php * sample_weight))
            OVER (PARTITION BY region_code)                  AS region_total_income,
        COUNT(*)                                             AS hh_count
    FROM ranked
    GROUP BY region_code, region_name, decile
)

SELECT
    region_code,
    region_name,
    decile,
    ROUND((decile_income_wt / region_total_income * 100)::NUMERIC, 2) AS income_share_pct,
    hh_count,

    -- Bottom 20% = deciles 1+2, Top 20% = deciles 9+10
    CASE
        WHEN decile <= 2  THEN 'bottom_20'
        WHEN decile >= 9  THEN 'top_20'
        ELSE 'middle_60'
    END AS income_group,

    -- Palma ratio numerator/denominator flagging
    CASE WHEN decile = 10 THEN decile_income_wt END AS top_10pct_income,
    CASE WHEN decile <= 4 THEN decile_income_wt END AS bottom_40pct_income

FROM weighted
ORDER BY region_code, decile;
