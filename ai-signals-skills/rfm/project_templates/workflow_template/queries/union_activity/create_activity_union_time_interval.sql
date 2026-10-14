WITH T1 as (
SELECT * FROM ${src_table.database}.${src_table.source}
WHERE TD_INTERVAL(${src_table.date_field}, '${lookback_period}/${time_interval_start_date}') 
)
SELECT ${src_table.join_key} AS ${globals.canonical_id},
MAX(${src_table.date_field}) as time,
TD_TIME_STRING(MAX(${src_table.date_field}), 's!') as latest_tstamp,
'${src_table.name}' AS source,
count(*) as total_touchpoints,
SUM(TRY(CAST(${src_table.order_amount} AS DOUBLE))) as total_spend,
(${session_unixtime} - MAX(${src_table.date_field}))/86400 AS recency_days
FROM T1
${src_table.filter_clause}
GROUP BY 1
