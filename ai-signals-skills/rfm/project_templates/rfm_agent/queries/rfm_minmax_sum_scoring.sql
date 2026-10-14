with rfm as (
  SELECT 
   ${globals.canonical_id},
   COALESCE(min(recency_days),0) AS recency,
   COALESCE(sum(total_touchpoints),0) as frequency,
   IF(COALESCE(sum(total_spend),0) < 0, 0, COALESCE(sum(total_spend),0)) as monetary 
   ,
   ROUND(1.0/(1.0 + COALESCE((CAST(1667489161 as BIGINT) - max_by(time,time))/86400,-1)),4) as R,
        ROUND(1.0+ COALESCE(max(total_touchpoints),0),0) as F,
        ROUND(SQRT(1.0+COALESCE(max(total_spend),0)),3) as M
FROM ${globals.activity_table}
group by 1
),

rfm_score as (
  SELECT *,
'minmax' as scaling_type,
 'product' as rfm_calc_type,
   ROUND(ROUND((r - (select min(r) from rfm))/((select max(r) from rfm) - (select min(r) from rfm)),3) +
          ROUND((f - (select min(f) from rfm))/((select max(f) from rfm) - (select min(f) from rfm)),3) +
          ROUND((m - (select min(m) from rfm))/((select max(m) from rfm) - (select min(m) from rfm)),3) ,3) as rfm_score
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

