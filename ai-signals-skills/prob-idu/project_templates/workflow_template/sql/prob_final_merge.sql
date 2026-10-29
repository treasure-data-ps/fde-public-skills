WITH base_cdp AS (
  SELECT 
    ${cluster_col_name},
    ${id_col},
    SPLIT_PART(${id_col}, '~', 1) AS base_cdp_id,
    avg_cluster_similarity,
    ${td.last_results.merge_cols}
  FROM ${output_table}
),

-- Create union-find structure: each CDP points to all CDPs in same prob_id
cdp_neighbors AS (
  SELECT 
    a.base_cdp_id,
    ARRAY_AGG(DISTINCT b.base_cdp_id) AS neighbors
  FROM base_cdp a
  INNER JOIN base_cdp b ON a.${cluster_col_name} = b.${cluster_col_name}
  GROUP BY a.base_cdp_id
),

-- Iteration 1
iter1 AS (
  SELECT 
    cn.base_cdp_id,
    ARRAY_AGG(DISTINCT neighbor_of_neighbor) AS extended_neighbors
  FROM cdp_neighbors cn
  CROSS JOIN UNNEST(cn.neighbors) AS t1(neighbor)
  LEFT JOIN cdp_neighbors cn2 ON neighbor = cn2.base_cdp_id
  CROSS JOIN UNNEST(COALESCE(cn2.neighbors, ARRAY[neighbor])) AS t2(neighbor_of_neighbor)
  GROUP BY cn.base_cdp_id
),

-- Iteration 2
iter2 AS (
  SELECT 
    i1.base_cdp_id,
    ARRAY_AGG(DISTINCT neighbor_of_neighbor) AS extended_neighbors
  FROM iter1 i1
  CROSS JOIN UNNEST(i1.extended_neighbors) AS t1(neighbor)
  LEFT JOIN iter1 i2 ON neighbor = i2.base_cdp_id
  CROSS JOIN UNNEST(COALESCE(i2.extended_neighbors, ARRAY[neighbor])) AS t2(neighbor_of_neighbor)
  GROUP BY i1.base_cdp_id
),

-- Iteration 3
iter3 AS (
  SELECT 
    i1.base_cdp_id,
    ARRAY_AGG(DISTINCT neighbor_of_neighbor) AS extended_neighbors
  FROM iter2 i1
  CROSS JOIN UNNEST(i1.extended_neighbors) AS t1(neighbor)
  LEFT JOIN iter2 i2 ON neighbor = i2.base_cdp_id
  CROSS JOIN UNNEST(COALESCE(i2.extended_neighbors, ARRAY[neighbor])) AS t2(neighbor_of_neighbor)
  GROUP BY i1.base_cdp_id
),

-- Assign cluster (minimum CDP in connected component)
cdp_to_cluster AS (
  SELECT 
    base_cdp_id,
    ARRAY_MIN(extended_neighbors) AS cluster_id
  FROM iter3
),

-- Count how many unique CDP IDs are in each cluster
cluster_sizes AS (
  SELECT 
    cluster_id,
    COUNT(DISTINCT base_cdp_id) AS cdp_count
  FROM cdp_to_cluster
  GROUP BY cluster_id
  HAVING COUNT(DISTINCT base_cdp_id) >= 2  -- Only keep clusters with 2+ CDP IDs
),

-- Filter to only valid clusters
valid_clusters AS (
  SELECT 
    ctc.base_cdp_id,
    ctc.cluster_id
  FROM cdp_to_cluster ctc
  INNER JOIN cluster_sizes cs ON ctc.cluster_id = cs.cluster_id
),

-- Aggregate each CDP's own data (not the entire cluster)
cdp_aggregated_data AS (
  SELECT 
    b.base_cdp_id,
    vc.cluster_id,
    MAX(b.avg_cluster_similarity) AS avg_cluster_similarity,
    ${td.last_results.merge_agg_cols}
  FROM base_cdp b
  INNER JOIN valid_clusters vc ON b.base_cdp_id = vc.base_cdp_id
  GROUP BY b.base_cdp_id, vc.cluster_id
),

-- Assign unified prob_id to the cluster
cluster_prob_id AS (
  SELECT 
    vc.cluster_id,
    MIN(b.${cluster_col_name}) AS unified_prob_id
  FROM base_cdp b
  INNER JOIN valid_clusters vc ON b.base_cdp_id = vc.base_cdp_id
  GROUP BY vc.cluster_id
),

-- Final result: each CDP with its own data but same prob_id
final_result AS (
  SELECT 
    cp.unified_prob_id AS ${cluster_col_name},
    cad.base_cdp_id AS ${id_col},
    cad.avg_cluster_similarity,
    ${td.last_results.merge_final_cols}
  FROM cdp_aggregated_data cad
  INNER JOIN cluster_prob_id cp ON cad.cluster_id = cp.cluster_id
)

SELECT * FROM final_result

