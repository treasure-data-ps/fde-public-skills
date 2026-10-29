-- Builds the column lists for prob_final_merge.sql from whatever attribute columns exist in ${output_table}
SELECT
  ARRAY_JOIN(ARRAY_AGG(column_name ORDER BY ordinal_position), ', ') AS merge_cols,
  ARRAY_JOIN(ARRAY_AGG(
    'ARRAY_JOIN(ARRAY_AGG(DISTINCT CAST(b.' || column_name || ' AS VARCHAR)) FILTER (WHERE b.' || column_name
    || ' IS NOT NULL AND TRIM(CAST(b.' || column_name || ' AS VARCHAR)) NOT IN ('''', '','')), chr(59) || '' '') AS ' || column_name
    ORDER BY ordinal_position), ', ') AS merge_agg_cols,
  ARRAY_JOIN(ARRAY_AGG('cad.' || column_name ORDER BY ordinal_position), ', ') AS merge_final_cols
FROM information_schema.columns
WHERE table_schema = '${sink_database}'
  AND table_name = '${output_table}'
  AND column_name NOT IN ('time', '${cluster_col_name}', '${id_col}', 'avg_cluster_similarity')
