SELECT 
  'Top_K_similar: ' || '${topk_similar_items}' || ', Recent_purchases: ' || '${recent_items}' || ', Max_recommended: ' || '${max_recommended_items}'  || ', Similarity_min: ' || '${dimsum_similarity_threshold}' AS model_params,
  'None' AS model_metrics