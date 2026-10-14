SELECT 
  '${td.each.src_table}' AS src_table,
  '${td.each.table_description}' AS table_description,
  '${td.each.final_where_clause}' as filter_clause,
  ${td.each.event_type} AS event_type,
  ARRAY_JOIN(ARRAY_AGG(ARRAY_DISINCT(${td.each.context_col})), ', ') as context_values,
  TD_TIME_STRING(MIN(${td.each.unixtime_col}), 'd!') AS min_date,
  TD_TIME_STRING(MIN(${td.each.unixtime_col}), 'd!') AS max_date,
  APPROX_DISTINCT(${unique_user_id}) as total_profiles,
  COUNT(*) as total_events
  FROM ${td.each.src_table}
  ${td.each.final_where_clause}
  GROUP BY 1, 2, 3, 4
  ORDER BY COUNT(*) LIMIT 10