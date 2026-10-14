WITH percentiles AS (
  SELECT
    -- Recency and frequency from all customers
    (SELECT approx_percentile(recency, ARRAY[0.25, 0.5, 0.75])
     FROM ${input_table}) AS recency_p,
    (SELECT approx_percentile(CAST(frequency AS DOUBLE), ARRAY[0.25, 0.5, 0.75])
     FROM ${input_table}) AS frequency_p,

    -- Monetary percentiles only for values > 0.05
    (SELECT approx_percentile(monetary_value, ARRAY[0.25, 0.5, 0.75])
     FROM ${input_table}
     WHERE monetary_value > 0.05) AS monetary_p
)

, BASE AS (
  SELECT 
    i.${globals.canonical_id},
    i.recency,
    i.frequency,
    i.monetary_value,
    
    -- Recency quartile (lower = better → reverse scale)
    CASE
      WHEN i.recency <= p.recency_p[1] THEN 4
      WHEN i.recency <= p.recency_p[2] THEN 3
      WHEN i.recency <= p.recency_p[3] THEN 2
      ELSE 1
    END AS r_quartile,

    -- Frequency quartile (higher = better)
    CASE
      WHEN CAST(i.frequency AS DOUBLE) <= p.frequency_p[1] THEN 1
      WHEN CAST(i.frequency AS DOUBLE) <= p.frequency_p[2] THEN 2
      WHEN CAST(i.frequency AS DOUBLE) <= p.frequency_p[3] THEN 3
      ELSE 4
    END AS f_quartile,

    -- Monetary quartile (higher = better)
    CASE
      WHEN i.monetary_value <= p.monetary_p[1] THEN 1
      WHEN i.monetary_value <= p.monetary_p[2] THEN 2
      WHEN i.monetary_value <= p.monetary_p[3] THEN 3
      ELSE 4
    END AS m_quartile

  FROM ${input_table} i
  CROSS JOIN percentiles p
)

SELECT
  BASE.*,
  'R' || CAST(r_quartile AS VARCHAR) || 
  'F' || CAST(f_quartile AS VARCHAR) || 
  'M' || CAST(m_quartile AS VARCHAR) AS rfm_quartile,
  ROUND((r_quartile + f_quartile + m_quartile) * 1.0 / 3.0, 2) AS rfm_score,
  CASE
    WHEN r_quartile = 4 AND f_quartile = 4 AND m_quartile = 4 THEN 'Champions'
    WHEN r_quartile >= 3 THEN
      CASE
        WHEN f_quartile >= 3 AND m_quartile >= 3 THEN 'Loyal Customers'
        WHEN f_quartile >= 2 AND m_quartile >= 2 THEN 'Potential Loyalists'
        WHEN f_quartile >= 2 OR m_quartile >= 2 THEN 'Promising'
        ELSE 'New Customers'
      END
    WHEN r_quartile = 2 THEN
      CASE
        WHEN m_quartile >= 3 THEN 'Cannot lose them'
        WHEN m_quartile = 2 AND f_quartile >= 2 THEN 'Need attention'
        ELSE 'Hibernating'
      END
    WHEN r_quartile = 1 THEN
      CASE
        WHEN m_quartile >= 3 OR (m_quartile = 2 AND f_quartile >= 2) THEN 'High Value Sleeping'
        ELSE 'Lost customers'
      END
    ELSE NULL
  END AS rfm_segment
FROM BASE