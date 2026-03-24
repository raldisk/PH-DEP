-- keyword_volume: top hashtags and mentions by day
-- Drives keyword cloud in Streamlit dashboard

WITH hashtag_exploded AS (
    SELECT
        day_manila,
        LOWER(TRIM(tag)) AS keyword,
        'hashtag'        AS keyword_type,
        sentiment_label
    FROM {{ ref('stg_tweet_events') }},
         UNNEST(hashtags) AS tag
    WHERE hashtags IS NOT NULL
      AND ARRAY_LENGTH(hashtags, 1) > 0
),

mention_exploded AS (
    SELECT
        day_manila,
        LOWER(TRIM(mention)) AS keyword,
        'mention'            AS keyword_type,
        sentiment_label
    FROM {{ ref('stg_tweet_events') }},
         UNNEST(mentions) AS mention
    WHERE mentions IS NOT NULL
      AND ARRAY_LENGTH(mentions, 1) > 0
),

combined AS (
    SELECT * FROM hashtag_exploded
    UNION ALL
    SELECT * FROM mention_exploded
),

aggregated AS (
    SELECT
        day_manila,
        keyword,
        keyword_type,
        COUNT(*)                                                          AS occurrences,
        SUM(CASE WHEN sentiment_label = 'positive' THEN 1 ELSE 0 END)   AS positive_tweets,
        SUM(CASE WHEN sentiment_label = 'negative' THEN 1 ELSE 0 END)   AS negative_tweets,
        RANK() OVER (
            PARTITION BY day_manila, keyword_type
            ORDER BY COUNT(*) DESC
        ) AS daily_rank
    FROM combined
    WHERE keyword != ''
      AND LENGTH(keyword) > 1
    GROUP BY 1, 2, 3
)

SELECT
    day_manila,
    keyword,
    keyword_type,
    occurrences,
    positive_tweets,
    negative_tweets,
    daily_rank,

    -- Sentiment tilt for this keyword
    CASE
        WHEN positive_tweets > negative_tweets THEN 'positive'
        WHEN negative_tweets > positive_tweets THEN 'negative'
        ELSE 'neutral'
    END AS sentiment_tilt

FROM aggregated
WHERE daily_rank <= 50   -- top 50 per day per type
ORDER BY day_manila DESC, keyword_type, daily_rank
