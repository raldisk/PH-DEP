-- stg_tweet_events: clean, deduplicate, normalize timestamps to Asia/Manila
-- Source: raw.tweet_events

WITH source AS (
    SELECT
        tweet_id,
        created_at,
        text,
        author_id,
        lang,
        hashtags,
        mentions,
        source,
        sentiment_label,
        sentiment_score,
        topic_name,
        loaded_at,
        ROW_NUMBER() OVER (PARTITION BY tweet_id ORDER BY loaded_at DESC) AS rn
    FROM raw.tweet_events
    WHERE text IS NOT NULL
      AND LENGTH(TRIM(text)) > 0
),

deduped AS (
    SELECT * FROM source WHERE rn = 1
)

SELECT
    tweet_id,

    -- Normalize to Asia/Manila (UTC+8)
    (created_at AT TIME ZONE 'UTC' AT TIME ZONE 'Asia/Manila') AS created_at_manila,
    created_at                                                   AS created_at_utc,

    TRIM(text)                    AS text,
    author_id,
    LOWER(lang)                   AS lang,
    hashtags,
    mentions,
    source,
    sentiment_label,
    sentiment_score,
    topic_name,

    -- Derived time buckets (Manila time)
    DATE_TRUNC('hour', created_at AT TIME ZONE 'UTC' AT TIME ZONE 'Asia/Manila')
                                  AS hour_manila,
    DATE_TRUNC('day',  created_at AT TIME ZONE 'UTC' AT TIME ZONE 'Asia/Manila')
                                  AS day_manila

FROM deduped
