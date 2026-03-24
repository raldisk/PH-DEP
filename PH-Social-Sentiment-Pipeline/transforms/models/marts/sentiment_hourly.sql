-- sentiment_hourly: per-topic positive/negative/neutral counts by hour (Manila time)
-- Primary source for the sentiment time-series chart in Streamlit

WITH base AS (
    SELECT
        hour_manila,
        topic_name,
        sentiment_label,
        COUNT(*) AS tweet_count
    FROM {{ ref('stg_tweet_events') }}
    WHERE sentiment_label IS NOT NULL
      AND topic_name      IS NOT NULL
    GROUP BY 1, 2, 3
),

pivoted AS (
    SELECT
        hour_manila,
        topic_name,
        SUM(CASE WHEN sentiment_label = 'positive' THEN tweet_count ELSE 0 END) AS positive,
        SUM(CASE WHEN sentiment_label = 'neutral'  THEN tweet_count ELSE 0 END) AS neutral,
        SUM(CASE WHEN sentiment_label = 'negative' THEN tweet_count ELSE 0 END) AS negative,
        SUM(tweet_count)                                                          AS total
    FROM base
    GROUP BY 1, 2
)

SELECT
    hour_manila,
    topic_name,
    positive,
    neutral,
    negative,
    total,

    -- Net sentiment score: (positive - negative) / total
    CASE WHEN total > 0
         THEN ROUND(((positive - negative)::NUMERIC / total), 4)
    END AS sentiment_score,

    -- Velocity: change in total vs previous hour for same topic
    total - LAG(total) OVER (
        PARTITION BY topic_name ORDER BY hour_manila
    ) AS velocity

FROM pivoted
ORDER BY hour_manila DESC, total DESC
