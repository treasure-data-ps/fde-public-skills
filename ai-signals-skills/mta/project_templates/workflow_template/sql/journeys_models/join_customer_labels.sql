-- Join customer labels to journey table
-- This enriches the journey data with customer segmentation or other labels from the customer table

SELECT
  J.*,
  C.${label_col}
FROM ${sink_database}.${output_tables.journeys_table} J
LEFT JOIN ${customers_table} C
  ON J.${unique_user_id} = C.${unique_user_id}
