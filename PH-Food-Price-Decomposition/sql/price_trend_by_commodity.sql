-- price_trend_by_commodity.sql
-- Monthly average price per commodity with cumulative change and YoY growth
-- Source: raw.psa_price_situationer

WITH monthly AS (
    SELECT
        DATE_TRUNC('month', price_date)::DATE  AS month,
        commodity_slug,
        commodity,
        AVG(retail_price_php)                  AS avg_price,
        STDDEV(retail_price_php)               AS price_stddev,
        COUNT(*)                               AS obs_count
    FROM raw.psa_price_situationer
    WHERE region = 'National'
    GROUP BY 1, 2, 3
),

with_lags AS (
    SELECT
        month,
        commodity_slug,
        commodity,
        avg_price,
        price_stddev,
        obs_count,

        -- YoY change
        LAG(avg_price, 12) OVER (
            PARTITION BY commodity_slug ORDER BY month
        ) AS price_12m_ago,

        -- First value for cumulative change base
        FIRST_VALUE(avg_price) OVER (
            PARTITION BY commodity_slug ORDER BY month
            ROWS BETWEEN UNBOUNDED PRECEDING AND CURRENT ROW
        ) AS first_price
    FROM monthly
)

SELECT
    month,
    commodity_slug,
    commodity,
    ROUND(avg_price::NUMERIC, 2)       AS avg_price,
    ROUND(price_stddev::NUMERIC, 4)    AS price_stddev,
    obs_count,

    -- YoY % change
    CASE WHEN price_12m_ago > 0
         THEN ROUND(((avg_price - price_12m_ago) / price_12m_ago * 100)::NUMERIC, 2)
    END                                AS yoy_change_pct,

    -- Cumulative % change from first observation
    CASE WHEN first_price > 0
         THEN ROUND(((avg_price - first_price) / first_price * 100)::NUMERIC, 2)
    END                                AS cumulative_change_pct

FROM with_lags
ORDER BY commodity_slug, month;
