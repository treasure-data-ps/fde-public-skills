WITH BASE AS (
  SELECT session_id, 
  MAX(run_date) as event_time
  FROM prob_model_table_params
  GROUP BY 1
)
SELECT session_id, 
DENSE_RANK() OVER (order by session_id DESC) as session_rnk, 
event_time
FROM  BASE