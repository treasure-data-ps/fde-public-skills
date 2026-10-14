with rfm as (
  SELECT 
   ${globals.canonical_id},
   COALESCE(min(recency_days),0) AS recency,
   COALESCE(sum(total_touchpoints),0) as frequency,
   IF(COALESCE(sum(total_spend),0) < 0, 0, COALESCE(sum(total_spend),0)) as monetary 

FROM ${globals.activity_table}
group by 1
),

rfm_score as (
  SELECT *,
'ln' as scaling_type,
 'sum' as rfm_calc_type,
Round(ROUND(1.0 / (1.0 + ln(recency+1.5)), 3) +
ROUND(ln(frequency+1.5), 3) +
ROUND(ln(monetary+1.5), 3) ,3) as rfm_score
from rfm

),
rfm_stats as
 (
SELECT r.* , 
rs.monetary_top_buyers
        ,CASE WHEN (r.monetary = 0 OR r.monetary>= rs.monetary_top_buyers OR r.FREQUENCY = 0)
              THEN 1 ELSE 0 END as exclude
        ,CASE WHEN (r.MONETARY = 0) THEN '${tier_labels.no_orders}'
              WHEN (r.FREQUENCY = 0) THEN '${tier_labels.no_activity}'
              WHEN (r.MONETARY >= rs.monetary_top_buyers) THEN '${tier_labels.monetary_outliers}' END as exclude_reason
  FROM rfm_score r
  CROSS JOIN (SELECT CAST(FLOOR(APPROX_PERCENTILE(c.MONETARY,${params.top_buyers_perc})/100)*100 as INTEGER) as monetary_top_buyers
              FROM rfm c  WHERE c.MONETARY > 0 ) rs
),
rfm_final AS
 (
  SELECT * 
        ,(SELECT ROUND(APPROX_PERCENTILE(rfm_score,${params.high_perc}),3) FROM rfm_stats WHERE exclude = 0) as high_threshold
        ,(SELECT ROUND(APPROX_PERCENTILE(rfm_score,${params.medium_perc}),3) FROM rfm_stats WHERE exclude = 0) as med_threshold
  FROM rfm_stats
  )
SELECT rfm_final.*
  
    ,COALESCE(exclude_reason
            ,CASE WHEN rfm_score >= high_threshold THEN 'High' 
                  WHEN rfm_score >= med_threshold THEN 'Med' 
             ELSE 'Low' END
      ) as RFM_Tier
FROM rfm_final

