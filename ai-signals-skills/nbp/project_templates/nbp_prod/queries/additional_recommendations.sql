WITH all_items as (
  SELECT * FROM ${prefix}supp_transactions
  -- SELECT ${original_user_id_column_name}, 
  --   ELEMENT_AT(SPLIT(td_url, '/'), -1) as itemid, 
  --   'favorited' as source,
  --   createdtime_tm FROM gld_prod.favorite_events
  -- UNION ALL 
  -- SELECT ${original_user_id_column_name}, 
  --   ELEMENT_AT(SPLIT(td_url, '/'), -1) as itemid, 
  --   'added_to_cart' as source,
  --   createdtime_tm FROM gld_prod.add_cart_events

  -- include the item filters in the query before
)
,
items as (
  SELECT ${original_user_id_column_name}, 
  itemid, 
  MAX_BY(source, createdtime_tm) as source, 
  MAX(createdtime_tm) as createdtime_tm FROM all_items
  GROUP BY 1, 2
)
,
purchased as (
  SELECT ${original_user_id_column_name}, 
    ARRAY_AGG(item) as bought
  FROM gld_prod.customer_orders 
  WHERE ${original_user_id_column_name} IN (SELECT DISTINCT ${original_user_id_column_name} FROM items)
  GROUP BY 1
)
,
recs as (
  SELECT items.* FROM items 
  LEFT JOIN purchased on items.${original_user_id_column_name}=purchased.${original_user_id_column_name}
  WHERE NOT CONTAINS(bought, itemid)
)

SELECT *, rank() OVER (
  PARTITION BY ${original_user_id_column_name} ORDER BY createdtime_tm DESC) as most_recent
FROM recs 