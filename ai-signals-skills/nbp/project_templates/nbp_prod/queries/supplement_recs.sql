WITH addl as (SELECT ${original_user_id_column_name}, 
  ARRAY_AGG(itemid) as new_items
FROM ${prefix}additional_recommendations
GROUP BY 1)

SELECT COALESCE(${original_user_id_column_name}, ${prefix}topk_recommended_items_temp2.userid) as ${original_user_id_column_name}, 
 rec_items as original_rec_items, 
 new_items, 
 SLICE(CONCAT(COALESCE(rec_items, ARRAY []), COALESCE(new_items, ARRAY [])), 1, 5) as rec_items
FROM ${prefix}topk_recommended_items_temp2
FULL OUTER JOIN addl ON addl.${original_user_id_column_name}=${prefix}topk_recommended_items_temp2.userid
ORDER BY CARDINALITY(rec_items)