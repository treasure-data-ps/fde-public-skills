SELECT 
CAST(CURRENT_DATE AS VARCHAR) as event_date, 
${session_unixtime} as unixtime_tstamp,
(SELECT APPROX_DISTINCT(userid) FROM ${prefix}transaction) as distinct_users_transactions_table,
COUNT(*) FROM 


SELECT ARRAY_JOIN(product_recommendations, ', ') as item_recs_combo,
        ARRAY_JOIN(product_categories, ', ') as category_recs_combo,
        COUNT(*) as event_cnt
        FROM ${user_master_attr_table}
        GROUP BY 1, 2
        order by 3
