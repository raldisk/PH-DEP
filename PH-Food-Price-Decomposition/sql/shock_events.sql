-- shock_events.sql
-- Identify price shocks as observations where the STL residual exceeds 2σ
-- Annotated with known historical events for narrative context
-- NOTE: STL decomposition runs in Python (statsmodels); this query works on
-- the pre-computed residuals table populated by notebook 05.

-- ── Known shock event reference table ────────────────────────────────────────
WITH shock_events (event_date, event_name, commodities_affected) AS (
    VALUES
        ('2008-07-01'::DATE, 'Global Food Crisis 2008',           'rice,wheat,cooking_oil'),
        ('2009-01-01'::DATE, 'Global Financial Crisis 2009',      'all'),
        ('2011-03-01'::DATE, 'Japan Earthquake + nuclear',        'fish,vegetables'),
        ('2019-03-01'::DATE, 'Rice Tariffication Law (RA 11203)', 'rice'),
        ('2020-03-01'::DATE, 'COVID-19 lockdown (ECQ)',           'all'),
        ('2021-03-01'::DATE, 'Suez Canal blockage',              'cooking_oil,wheat'),
        ('2022-02-01'::DATE, 'Ukraine war (Russia invasion)',     'cooking_oil,wheat,fuel'),
        ('2023-01-01'::DATE, 'Onion Crisis (smuggling crackdown)','onion,garlic'),
        ('2023-07-01'::DATE, 'El Niño rice supply impact',       'rice,vegetables')
),

-- ── Monthly residuals from STL (populated by notebook 05) ─────────────────
residuals AS (
    SELECT
        month,
        commodity_slug,
        residual,
        AVG(residual)    OVER (PARTITION BY commodity_slug) AS mean_resid,
        STDDEV(residual) OVER (PARTITION BY commodity_slug) AS std_resid
    FROM raw.stl_residuals   -- created by notebook 05
    WHERE residual IS NOT NULL
),

flagged AS (
    SELECT
        month,
        commodity_slug,
        ROUND(residual::NUMERIC, 4)     AS residual,
        ROUND(mean_resid::NUMERIC, 4)   AS mean_resid,
        ROUND(std_resid::NUMERIC, 4)    AS std_resid,
        ROUND(ABS((residual - mean_resid) / NULLIF(std_resid, 0))::NUMERIC, 3)
                                        AS z_score,
        ABS(residual - mean_resid) > 2 * NULLIF(std_resid, 0)
                                        AS is_shock
    FROM residuals
)

SELECT
    f.month,
    f.commodity_slug,
    f.residual,
    f.z_score,
    f.is_shock,
    e.event_name,
    e.event_date,
    e.commodities_affected
FROM flagged f
LEFT JOIN shock_events e
    ON f.month BETWEEN e.event_date AND (e.event_date + INTERVAL '3 months')::DATE
    AND (e.commodities_affected LIKE '%' || f.commodity_slug || '%'
         OR e.commodities_affected = 'all')
WHERE f.is_shock = TRUE
ORDER BY f.month, f.z_score DESC;
