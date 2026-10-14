WITH train_latest AS (
        SELECT
         
            MAX(session_id) AS train_session_id
        FROM ${table_prefix}train_run_log
    ),
    pred_latest AS (
        SELECT
   
            MAX(session_id) AS pred_session_id
        FROM ${table_prefix}final_features_${mode}
    )
    SELECT
       t.train_session_id  as train_batch_id,
        t.train_session_id,
        p.pred_session_id as pred_batch_id,
        p.pred_session_id
    FROM train_latest t
    CROSS JOIN pred_latest p