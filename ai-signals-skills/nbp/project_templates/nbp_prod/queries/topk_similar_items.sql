SELECT
  ii.itemid, 
  to_ordered_list(item_id, score, '-reverse -k ${max_recommended_items}') as similar_items
FROM
  ${prefix}item_similarity

JOIN ${prefix}itemid_name_product_mapping ii 
  ON ii.itemid=${prefix}item_similarity.target_item_id 
GROUP BY 
  ii.itemid