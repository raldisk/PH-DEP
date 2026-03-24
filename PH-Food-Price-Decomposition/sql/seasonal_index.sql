-- seasonal_index.sql
-- Seasonal index per commodity per month (ratio to 12-month centered moving average)
-- Reveals intra-year price patterns: harvest cycles, typhoon season, back-to-school

WITH monthly AS (
    SELECT
        DATE_TRUNC('month', price_date)::DATE AS month,
        commodity_slug,
        AVG(retail_price_php)                 AS avg_price
    FROM raw.psa_price_situationer
    WHERE region = 'National'
    GROUP BY 1, 2
),

cma AS (
    SELECT
        month,
        commodity_slug,
        avg_price,
        -- 12-month centered moving average (6 before + current + 5 after)
        AVG(avg_price) OVER (
            PARTITION BY commodity_slug
            ORDER BY month
            ROWS BETWEEN 5 PRECEDING AND 6 FOLLOWING
        ) AS centered_ma_12
    FROM monthly
),

with_index AS (
    SELECT
        month,
        commodity_slug,
        ROUND(avg_price::NUMERIC, 2)                                     AS avg_price,
        ROUND(centered_ma_12::NUMERIC, 2)                                AS centered_ma_12,
        CASE WHEN centered_ma_12 > 0
             THEN ROUND((avg_price / centered_ma_12)::NUMERIC, 4)
        END                                                               AS seasonal_index,
        EXTRACT(MONTH FROM month)::INT                                    AS month_num,
        TO_CHAR(month, 'Mon')                                             AS month_name
    FROM cma
    WHERE centered_ma_12 IS NOT NULL
)

SELECT
    month,
    commodity_slug,
    avg_price,
    centered_ma_12,
    seasonal_index,
    month_num,
    month_name,

    -- Average seasonal index per month across all years (the seasonal pattern)
    ROUND(AVG(seasonal_index) OVER (
        PARTITION BY commodity_slug, month_num
    )::NUMERIC, 4)                                                        AS avg_seasonal_index,

    -- Flag: above-average price months (seasonal high)
    CASE WHEN seasonal_index > 1.05 THEN TRUE ELSE FALSE END             AS is_seasonal_high,
    CASE WHEN seasonal_index < 0.95 THEN TRUE ELSE FALSE END             AS is_seasonal_low

FROM with_index
ORDER BY commodity_slug, month;
