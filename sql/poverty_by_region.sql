-- poverty_by_region.sql
-- Regional poverty incidence pivot — 2018, 2021, 2023
-- Source: raw.poverty_provincial

SELECT
    region_code,
    region_name,

    -- Poverty incidence by year
    MAX(CASE WHEN year = 2018 THEN poverty_incidence END) AS pov_2018,
    MAX(CASE WHEN year = 2021 THEN poverty_incidence END) AS pov_2021,
    MAX(CASE WHEN year = 2023 THEN poverty_incidence END) AS pov_2023,

    -- Change columns
    ROUND(
        MAX(CASE WHEN year = 2023 THEN poverty_incidence END) -
        MAX(CASE WHEN year = 2021 THEN poverty_incidence END),
    2) AS change_2021_to_2023,

    ROUND(
        MAX(CASE WHEN year = 2023 THEN poverty_incidence END) -
        MAX(CASE WHEN year = 2018 THEN poverty_incidence END),
    2) AS change_2018_to_2023,

    -- Direction flag (improved / worsened)
    CASE
        WHEN MAX(CASE WHEN year = 2023 THEN poverty_incidence END) <
             MAX(CASE WHEN year = 2021 THEN poverty_incidence END)
        THEN 'improved'
        WHEN MAX(CASE WHEN year = 2023 THEN poverty_incidence END) >
             MAX(CASE WHEN year = 2021 THEN poverty_incidence END)
        THEN 'worsened'
        ELSE 'unchanged'
    END AS direction_2021_to_2023

FROM raw.poverty_provincial
WHERE province_code IS NULL  -- regional-level rows only
GROUP BY region_code, region_name
ORDER BY pov_2023 DESC NULLS LAST;
