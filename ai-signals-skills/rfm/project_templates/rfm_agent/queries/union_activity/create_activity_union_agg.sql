SELECT ${src_table.join_key} AS ${globals.canonical_id},
max(${src_table.date_field}) as time,
TD_TIME_STRING(max(${src_table.date_field}), 's!') as latest_tstamp,
'${src_table.name}' AS source,
count(*) as total_touchpoints,
SUM(TRY(CAST(${src_table.order_amount} AS DOUBLE))) as total_spend,
---below avoids negative recency if a bad tstamp that is greater than todays date is present in the dataset
IF(${session_unixtime} - MAX(${src_table.date_field}) < 0, 0, (${session_unixtime} - MAX(${src_table.date_field}))/86400) AS recency_days
FROM ${src_table.database}.${src_table.source}
${src_table.filter_clause}
GROUP BY 1