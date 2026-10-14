SELECT
  CAST(${session_unixtime} AS INTEGER) AS time,
  TD_TIME_STRING(${session_unixtime}, 's!') as run_time,
  day, 
  channels, 
  ROUND(value, 2) as value,
  round(value / SUM(value) OVER (PARTITION BY day), 3) AS percentage
FROM 
  mta_shapley_attribution
  where channels is not null
ORDER BY 
  day, 
  channels;