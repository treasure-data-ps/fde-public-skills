-- Model input table: one row per ${id_col}, written to ${input_table} by ml_prob_unification_launch.dig.
-- EXAMPLE STRUCTURE -- replace every <...> placeholder with the customer's tables and columns
-- before the first run (sql/README.md). Keep the output contract:
--   ${id_col}       one row per canonical ID, never NULL
--   dedupe columns  one column per entry of dedupe_columns in config/global.yml, same names, raw values
--                   (cleaned inside the blocking SQL by type)
-- Other columns are carried through to the output table.

SELECT
  <id_col>                         AS ${id_col},
  <phone_col>                      AS phone_key,
  <email_col>                      AS email_key,
  <address_col>                    AS address_key
FROM ${source_database}.${source_table}
WHERE <id_col> IS NOT NULL
