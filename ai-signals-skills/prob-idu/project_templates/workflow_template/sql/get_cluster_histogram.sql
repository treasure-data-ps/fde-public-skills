WITH T1 AS (
SELECT
${cluster_col_name}, count(*) as num_records_per_cluster
FROM dedupe_${output_table}
GROUP BY 1
)
,
CLUST AS (
SELECT
num_records_per_cluster,
COUNT(${cluster_col_name}) as cluster_cnt
FROM T1
GROUP BY 1
),
T2 AS (
SELECT
${block_key_col}, count(*) as num_records_per_block
FROM ${blocking_table}
GROUP BY 1
)
,
BLOCK AS (
SELECT
${session_id} as session_id,
num_records_per_block,
COUNT(${block_key_col}) as block_cnt
FROM T2
GROUP BY 2
)
SELECT
BLOCK.*, 
CLUST.num_records_per_cluster, 
CLUST.cluster_cnt
FROM BLOCK 
FULL OUTER JOIN CLUST
ON BLOCK.num_records_per_block = CLUST.num_records_per_cluster