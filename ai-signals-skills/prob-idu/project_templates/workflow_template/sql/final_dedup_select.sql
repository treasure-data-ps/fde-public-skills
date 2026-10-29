SELECT ARRAY_JOIN(ARRAY_AGG(column_name),',') as cols
FROM INFORMATION_SCHEMA.columns 
WHERE table_schema='${sink_database}' AND table_name='${output_table}'
AND column_name NOT IN ('time', '${cluster_col_name}', 'avg_cluster_similarity')