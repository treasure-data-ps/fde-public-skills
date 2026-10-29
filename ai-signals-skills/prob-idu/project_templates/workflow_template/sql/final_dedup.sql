WITH DEDUP AS (
  SELECT ${cluster_col_name}, COUNT(*) as num_ids
  FROM ${output_table}
  GROUP BY 1
)
,
G AS (
  SELECT f.*, DEDUP.num_ids
  FROM ${output_table} f
  JOIN DEDUP ON f.${cluster_col_name} = DEDUP.${cluster_col_name}
)

SELECT MAX_BY(${cluster_col_name}, num_ids) AS ${cluster_col_name}, 
  MAX_BY(avg_cluster_similarity, num_ids) as avg_cluster_similarity, 
  ${td.last_results.cols} 
FROM G
GROUP BY ${td.last_results.cols}