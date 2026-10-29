
-- @TD distribute_strategy: aggressive


-- Turns MinHash buckets into blocks: pairs sharing >= keygroups * jaccard_similarity_threshold buckets are blocked together

WITH 
-- Step 1: Generate pairs with counts
qualified_pairs AS (
  SELECT 
    L.${id_col},
    R.${id_col} AS ${id_col}s,
    COUNT(*) AS cnt
  FROM ${blocking_table}_temp L
  INNER JOIN ${blocking_table}_temp R
    ON L.clusterid = R.clusterid
  WHERE L.${id_col} < R.${id_col}
  GROUP BY L.${id_col}, R.${id_col}
  HAVING COUNT(*) >= CAST(ROUND(${keygroups} * ${jaccard_similarity_threshold}) AS INT)
),

-- Step 2: Create user sets efficiently using Hivemall array functions
user_sets AS (
  SELECT 
    ${id_col},
    sort_array(array_union(collect_list(${id_col}s), array(${id_col}))) AS userid_set
  FROM qualified_pairs
  GROUP BY ${id_col}
),

-- Step 3: Generate unique blocks with minimal memory
-- Using Hive-compatible block key generation
blocks AS (
  SELECT 
    CONCAT('block_', 
           CAST(row_number() OVER (ORDER BY size(userid_set) DESC) AS STRING), 
           '_', 
           CAST(unix_timestamp() AS STRING)) AS block_key,
    userid_set,
    row_number() OVER (ORDER BY size(userid_set) DESC) as rnk
  FROM (
    SELECT DISTINCT userid_set 
    FROM user_sets
  ) t
),

-- Step 4: Explode blocks efficiently using Hive's lateral view
block_members AS (
  SELECT
    block_key,
    member_id,
    rnk
  FROM blocks
  LATERAL VIEW explode(userid_set) exploded_table AS member_id
)

-- DIGDAG_INSERT_LINE
-- Step 5: Final output with original data
SELECT 
  bm.block_key,
  org.*,
  bm.rnk
FROM block_members bm
LEFT JOIN ${sink_database}.${input_table} org 
  ON bm.member_id = org.${id_col}
