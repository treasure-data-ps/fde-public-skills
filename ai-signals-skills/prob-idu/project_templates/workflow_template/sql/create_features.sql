WITH T1 as (
SELECT column_name FROM INFORMATION_SCHEMA.COLUMNS
WHERE TABLE_NAME = 'prob_hash_table' and TABLE_SCHEMA = '${sink_database}'
and column_name not in ('time','${id_col}','unified_contact_id','td_client_id')
)
SELECT 
array_join(array_sort(array_distinct(filter(array_agg(column_name), x -> x IS NOT NULL))), ', ') as column_names,
array_join(array_sort(array_distinct(filter(array_agg(CONCAT('"', column_name, '"')), x -> x IS NOT NULL))), ', ') as column_list

FROM T1