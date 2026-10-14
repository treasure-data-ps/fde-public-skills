WITH BASE AS (
( SELECT * FROM ${output_tables.journeys_table} WHERE conversion_value > 0 AND journey_touchpoints_total <= 50 AND TD_INTERVAL(time, '${ml_models_lookback_days_limit}/now'))
UNION ALL
( SELECT * FROM ${output_tables.journeys_table} WHERE conversion_value = 0 AND TD_INTERVAL(time, '${ml_models_lookback_days_limit}/now')  ORDER BY conversion_journey_id LIMIT 100000 )
)
SELECT * FROM BASE 
WHERE  journey_index = 1 OR journey_index > (journey_length - (${shapely_lookback_window} - 1))
AND TD_INTERVAL(time, '${ml_models_lookback_days_limit}/now')
ORDER BY conversion_value  desc, event_date desc
LIMIT ${ml_models_records_limit}

