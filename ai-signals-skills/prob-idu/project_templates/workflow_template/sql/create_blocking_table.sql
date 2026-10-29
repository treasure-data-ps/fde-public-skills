WITH T1 AS (
  
  SELECT ${id_col},${td.last_results.cleaning_query} FROM ${sink_database}.${input_table}${td.last_results.excl_suffix}
),

T2 AS (SELECT ${id_col}, ${td.last_results.blocking_query} from T1)

SELECT distinct B.* from ${sink_database}.${input_table} A LEFT JOIN T2 B ON A.${id_col} = B.${id_col}


