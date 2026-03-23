-- gini_trend.sql
-- National Gini trend approximation from FIES income data
-- Note: Official Gini values from PSA/World Bank used as anchor points.
-- This query computes a relative Gini approximation from FIES decile shares.

-- Step 1: Income decile shares by survey year
WITH deciles AS (
    SELECT
        survey_year,
        decile,
        SUM(total_income_php * sample_weight)           AS decile_income,
        SUM(SUM(total_income_php * sample_weight))
            OVER (PARTITION BY survey_year)             AS total_income
    FROM (
        SELECT 2021 AS survey_year, total_income_php, sample_weight,
               NTILE(10) OVER (ORDER BY total_income_php) AS decile
        FROM raw.fies_2021
        UNION ALL
        SELECT 2023, total_income_php, sample_weight,
               NTILE(10) OVER (ORDER BY total_income_php) AS decile
        FROM raw.fies_2023
    ) sub
    GROUP BY survey_year, decile
),

-- Step 2: Lorenz curve coordinates
lorenz AS (
    SELECT
        survey_year,
        decile,
        decile_income / total_income                    AS income_share,
        SUM(decile_income / total_income)
            OVER (PARTITION BY survey_year ORDER BY decile) AS cumulative_share,
        decile::NUMERIC / 10                            AS population_share
    FROM deciles
),

-- Step 3: Gini approximation (trapezoidal rule)
gini_approx AS (
    SELECT
        survey_year,
        ROUND(
            1 - 2 * SUM(
                (cumulative_share + LAG(cumulative_share, 1, 0) OVER (
                    PARTITION BY survey_year ORDER BY decile
                )) / 2 * 0.1
            ),
        4) AS gini_approx
    FROM lorenz
    GROUP BY survey_year
)

-- Final: combine with known anchor Gini values
SELECT
    g.survey_year                           AS year,
    g.gini_approx                           AS computed_gini,

    -- Official PSA/World Bank values for reference
    CASE g.survey_year
        WHEN 2021 THEN 0.4000
        WHEN 2023 THEN 0.3870
    END                                     AS official_gini,

    CASE
        WHEN g.survey_year = 2023
        THEN 'First year below 0.40 — milestone'
        ELSE NULL
    END                                     AS annotation

FROM gini_approx g
ORDER BY year;
