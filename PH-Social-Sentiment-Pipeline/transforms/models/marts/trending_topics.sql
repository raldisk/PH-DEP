-- trending_topics: topic volume + net sentiment score + velocity
-- Drives the "Top 10 Trending" panel in Streamlit

WITH tweet_vol AS (
    SELECT
        topic_name,
        day_manila,
        COUNT(*)                                       AS tweet_count,
        AVG(sentiment_score)                           AS avg_sentiment,
        SUM(CASE WHEN sentiment_label = 'positive' THEN 1 ELSE 0 END) AS positive_count,
        SUM(CASE WHEN sentiment_label = 'negative' THEN 1 ELSE 0 END) AS negative_count,
        SUM(CASE WHEN sentiment_label = 'neutral'  THEN 1 ELSE 0 END) AS neutral_count
    FROM {{ ref('stg_tweet_events') }}
    WHERE topic_name IS NOT NULL
    GROUP BY 1, 2
),

with_trend AS (
    SELECT
        topic_name,
        day_manila,
        tweet_count,
        ROUND(avg_sentiment::NUMERIC, 4)              AS avg_sentiment,
        positive_count,
        negative_count,
        neutral_count,

        -- Rank by volume within each day
        RANK() OVER (
            PARTITION BY day_manila
            ORDER BY tweet_count DESC
        ) AS daily_rank,

        -- Day-over-day volume change
        tweet_count - LAG(tweet_count) OVER (
            PARTITION BY topic_name
            ORDER BY day_manila
        ) AS volume_change_dod,

        -- Sentiment velocity (change vs previous day)
        ROUND((avg_sentiment - LAG(avg_sentiment) OVER (
            PARTITION BY topic_name
            ORDER BY day_manila
        ))::NUMERIC, 4) AS sentiment_velocity
    FROM tweet_vol
)

SELECT
    topic_name,
    day_manila,
    tweet_count,
    avg_sentiment,
    positive_count,
    negative_count,
    neutral_count,
    daily_rank,
    volume_change_dod,
    sentiment_velocity,

    -- Dominant sentiment for the day
    CASE
        WHEN positive_count >= negative_count AND positive_count >= neutral_count THEN 'positive'
        WHEN negative_count >= positive_count AND negative_count >= neutral_count THEN 'negative'
        ELSE 'neutral'
    END AS dominant_sentiment

FROM with_trend
ORDER BY day_manila DESC, daily_rank
