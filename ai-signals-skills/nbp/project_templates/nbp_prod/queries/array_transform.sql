SELECT user_id as userid, 
CAST(JSON_PARSE(REPLACE(rec_items, '''', '"')) AS array(varchar)) AS rec_items FROM 
${prefix}topk_recommended_items_temp