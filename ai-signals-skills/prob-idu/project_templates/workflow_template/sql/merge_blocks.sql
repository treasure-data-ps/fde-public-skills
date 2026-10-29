-- Merges duplicate blocks per ID and splits blocks larger than ${max_ids_per_block}
WITH merged_blocks AS (
    SELECT 
        block_key,
        ${id_col},
        ${td.last_results.column_list},
        rnk,
        ROW_NUMBER() OVER (
            PARTITION BY ${id_col} 
            ORDER BY rnk ASC  -- Choose record with lowest original rank
        ) as row_num
    FROM ${blocking_table}
),
deduplicated_blocks AS (
    SELECT 
        block_key,
        ${id_col},
       ${td.last_results.column_list},
        rnk as original_rnk
    FROM merged_blocks
    WHERE row_num = 1
),
block_sizes AS (
    SELECT 
        block_key,
        COUNT(*) as block_size
    FROM deduplicated_blocks
    GROUP BY block_key
),
split_large_blocks AS (
    SELECT 
        d.block_key,
        d.${id_col},
       ${td.last_results.column_list},
        d.original_rnk,
        bs.block_size,
        CASE 
            WHEN bs.block_size <= ${max_ids_per_block} THEN d.block_key
            ELSE d.block_key || '_' || CAST(CEILING(ROW_NUMBER() OVER (PARTITION BY d.block_key ORDER BY d.${id_col}) / ${max_ids_per_block}) AS VARCHAR)
        END as new_block_key,
        ROW_NUMBER() OVER (PARTITION BY d.block_key ORDER BY d.${id_col}) as block_position
    FROM deduplicated_blocks d
    JOIN block_sizes bs ON d.block_key = bs.block_key
)
SELECT 
    new_block_key as block_key,
    ${id_col},
    ${td.last_results.column_list},
    RANK() OVER (ORDER BY new_block_key) as rnk
FROM split_large_blocks
ORDER BY ${id_col}, new_block_key
