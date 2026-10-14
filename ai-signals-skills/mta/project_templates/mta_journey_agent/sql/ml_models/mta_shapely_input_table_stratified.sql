WITH journey_info AS (
  SELECT
    conversion_journey_id,
    MAX(journey_touchpoints_total) AS journey_touchpoints_total,
    MAX(channel_list_final) AS channel_list_final,
    MAX(conversion_value) AS conversion_value,
    COUNT(*) AS journey_rows
  FROM ${output_tables.journeys_table}
  GROUP BY 1
),
-- All converted journeys — take every single one
converted AS (
  SELECT conversion_journey_id, channel_list_final, journey_rows
  FROM journey_info
  WHERE conversion_value > 0.0 AND journey_touchpoints_total <= 15
),
converted_total_rows AS (
  SELECT SUM(journey_rows) AS converted_rows FROM converted
),
-- Remaining row budget for non-converted
remaining_budget AS (
  SELECT ${ml_models_records_limit} - converted_rows AS remaining_rows
  FROM converted_total_rows
),
-- Non-converted journeys with channel stats
non_converted AS (
  SELECT conversion_journey_id, channel_list_final, journey_rows
  FROM journey_info
  WHERE conversion_value = 0.0
),
nc_channel_stats AS (
  SELECT
    channel_list_final,
    SUM(journey_rows) AS total_channel_rows
  FROM non_converted
  GROUP BY 1
),
nc_num_channels AS (
  SELECT COUNT(*) AS n_channels FROM nc_channel_stats
),
-- Budget per channel for non-converted, with redistribution
nc_budget_calc AS (
  SELECT
    cs.channel_list_final,
    cs.total_channel_rows,
    rb.remaining_rows / nc.n_channels AS base_budget,
    LEAST(cs.total_channel_rows, rb.remaining_rows / nc.n_channels) AS capped_budget
  FROM nc_channel_stats cs
  CROSS JOIN nc_num_channels nc
  CROSS JOIN remaining_budget rb
),
nc_leftover AS (
  SELECT
    SUM(base_budget - capped_budget) AS leftover_rows,
    SUM(CASE WHEN total_channel_rows > base_budget THEN 1 ELSE 0 END) AS n_large_channels
  FROM nc_budget_calc
),
nc_final_budget AS (
  SELECT
    bc.channel_list_final,
    CASE
      WHEN bc.total_channel_rows <= bc.base_budget
        THEN bc.total_channel_rows
      ELSE LEAST(
        bc.total_channel_rows,
        bc.base_budget + COALESCE(lo.leftover_rows, 0) / GREATEST(lo.n_large_channels, 1)
      )
    END AS channel_row_limit
  FROM nc_budget_calc bc
  CROSS JOIN nc_leftover lo
),
-- Rank non-converted journeys within each channel randomly
ranked_non_converted AS (
  SELECT
    nc.*,
    SUM(nc.journey_rows) OVER (
      PARTITION BY nc.channel_list_final
      ORDER BY RANDOM()
      ROWS BETWEEN UNBOUNDED PRECEDING AND CURRENT ROW
    ) AS cumulative_rows
  FROM non_converted nc
),
selected_non_converted AS (
  SELECT rnc.conversion_journey_id
  FROM ranked_non_converted rnc
  JOIN nc_final_budget fb
    ON rnc.channel_list_final = fb.channel_list_final
  WHERE rnc.cumulative_rows <= fb.channel_row_limit
),
-- Combine: all converted + stratified non-converted
all_selected AS (
  SELECT conversion_journey_id FROM converted
  UNION ALL
  SELECT conversion_journey_id FROM selected_non_converted
)
SELECT t.*
FROM ${output_tables.journeys_table} t
JOIN all_selected s
  ON t.conversion_journey_id = s.conversion_journey_id