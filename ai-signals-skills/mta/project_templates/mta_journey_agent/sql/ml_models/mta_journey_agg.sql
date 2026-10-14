WITH T1 as (
  SELECT  td_time_string(max(time),'s!') as date_time,
conversion_journey_id ,
conversion_month,
array_join(array_agg(channel order by time),' > ') as journey ,
 max(conversion_flag) as conversion
from ${output_tables.journeys_table}
WHERE TD_INTERVAL(time, '${ml_models_lookback_days_limit}/now')
group by 2, 3
)
SELECT * from T1
order by conversion desc, date_time desc
limit ${ml_models_records_limit}
