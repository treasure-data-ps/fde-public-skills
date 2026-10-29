-- @TD distribute_strategy: aggressive

WITH 
-- Step 1: Direct feature generation
user_features AS (
  SELECT
    ${id_col},
    CATEGORICAL_FEATURES(
      array(${td.last_results.column_list}), 
      ${td.last_results.column_names}
    ) AS features
  FROM ${sink_database}.prob_hash_table 
),

-- Step 2: Generate MinHash signatures
user_hash_all AS (
  SELECT  
    minhash(${id_col}, features, "-n ${hashes} -k ${keygroups}") as (clusterId, ${id_col}) 
  FROM user_features
),

-- Step 3: Keep clusters of 2..max_ids_per_cluster IDs
valid_clusters AS (
  SELECT 
    clusterid, 
    COUNT(*) as cluster_size
  FROM user_hash_all
  GROUP BY clusterid
  HAVING COUNT(*) BETWEEN 2 AND ${max_ids_per_cluster}  -- Apply size limits early
)

-- DIGDAG_INSERT_LINE
-- Step 4: Final output with only valid clusters
SELECT 
  a.clusterid,
  a.${id_col}
FROM user_hash_all a
INNER JOIN valid_clusters b ON a.clusterid = b.clusterid;
