WITH t1 as (
  SELECT rank, tstamp, userid, cast(itemid as string)
  from ${prefix}recent_item_contacts 
),

topk as (
  select
    each_top_k(
       ${max_recommended_items}, userid, similarity,
       userid, item_id
    ) as (rank, similarity, userid, rec_item)
  from (
    select
      t1.userid, t2.item_id, max(t2.score) as similarity
    from t1
      JOIN ${prefix}item_similarity t2 ON (t1.itemid = t2.target_item_id)
    where
      t1.itemid != t2.item_id -- do not include items that user already purchased
      AND NOT EXISTS (
        SELECT a.itemid FROM ${prefix}user_item a
        WHERE a.userid = t1.userid AND a.itemid = t2.item_id
          AND a.count <= ${min_cooccurence_filter} -- optional filtering
      )
    group by
      t1.userid, t2.item_id
    CLUSTER BY
      userid -- top-k grouping by userid
  ) t1
)
-- DIGDAG_INSERT_LINE
select
  userid as user_id,
  to_ordered_list(rec_item, rank) as rec_items
from
  topk
group by
  userid
;