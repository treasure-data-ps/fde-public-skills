-- Single Comprehensive Analysis Query for Probabilistic Unification Table
-- Fixed for Presto compatibility
WITH base_stats AS (
    SELECT 
        CAST(COUNT(*) AS DOUBLE) as total_records,
        CAST(COUNT(DISTINCT ${cluster_col_name}) AS DOUBLE) as unique_prob_ids,
        CAST(COUNT(DISTINCT ${id_col}) AS DOUBLE) as unique_${id_col}s,
        AVG(avg_cluster_similarity) as avg_similarity_score,
        STDDEV(avg_cluster_similarity) as similarity_std_dev,
        MIN(avg_cluster_similarity) as min_similarity,
        MAX(avg_cluster_similarity) as max_similarity,
        APPROX_PERCENTILE(avg_cluster_similarity, 0.5) as median_similarity,
        APPROX_PERCENTILE(avg_cluster_similarity, 0.25) as q1_similarity,
        APPROX_PERCENTILE(avg_cluster_similarity, 0.75) as q3_similarity 
    FROM dedupe_${output_table}
),
quality_distribution AS (
    SELECT 
        CAST(SUM(CASE WHEN avg_cluster_similarity >= 0.98 THEN 1 ELSE 0 END) AS DOUBLE) as excellent_records,
        CAST(SUM(CASE WHEN avg_cluster_similarity >= 0.95 AND avg_cluster_similarity < 0.98 THEN 1 ELSE 0 END) AS DOUBLE) as very_good_records,
        CAST(SUM(CASE WHEN avg_cluster_similarity >= 0.90 AND avg_cluster_similarity < 0.95 THEN 1 ELSE 0 END) AS DOUBLE) as good_records,
        CAST(SUM(CASE WHEN avg_cluster_similarity >= 0.85 AND avg_cluster_similarity < 0.90 THEN 1 ELSE 0 END) AS DOUBLE) as fair_records,
        CAST(SUM(CASE WHEN avg_cluster_similarity < 0.85 THEN 1 ELSE 0 END) AS DOUBLE) as poor_records,
        CAST(COUNT(*) AS DOUBLE) as total_for_pct
    FROM dedupe_${output_table}
),
cluster_analysis AS (
    SELECT 
        AVG(CAST(cluster_size AS DOUBLE)) as avg_cluster_size,
        STDDEV(CAST(cluster_size AS DOUBLE)) as cluster_size_variance,
        MIN(cluster_size) as min_cluster_size,
        MAX(cluster_size) as max_cluster_size,
        AVG(CAST(${id_col}s_per_cluster AS DOUBLE)) as avg_${id_col}s_per_cluster,
        CAST(SUM(CASE WHEN ${id_col}s_per_cluster = 1 THEN 1 ELSE 0 END) AS DOUBLE) as pure_clusters,
        CAST(COUNT(*) AS DOUBLE) as total_clusters,
        AVG(avg_cluster_sim) as avg_intra_cluster_similarity
    FROM (
        SELECT 
            ${cluster_col_name},
            COUNT(*) as cluster_size,
            COUNT(DISTINCT ${id_col}) as ${id_col}s_per_cluster,
            AVG(avg_cluster_similarity) as avg_cluster_sim
        FROM dedupe_${output_table}
        GROUP BY ${cluster_col_name}
    ) cluster_metrics
)
SELECT 
${session_id} as session_id,
    -- Configuration identifier
    'dedupe_${output_table}' as table_name,
    
    -- CORE METRICS FOR COMPARISON
    CAST(bs.total_records AS BIGINT) as total_records,
    CAST(bs.unique_prob_ids AS BIGINT) as unique_prob_ids,
    CAST(bs.unique_${id_col}s AS BIGINT) as unique_${id_col}s,
    
    -- UNIFICATION EFFICIENCY (Higher = Better)
    ROUND(bs.total_records / bs.unique_${id_col}s, 2) as unification_compression_ratio,
    ROUND(bs.total_records / bs.unique_prob_ids, 2) as cluster_density_ratio,
    
    -- SIMILARITY QUALITY METRICS
    ROUND(bs.avg_similarity_score, 4) as avg_similarity_score,
    ROUND(bs.similarity_std_dev, 4) as similarity_consistency,
    ROUND(bs.median_similarity, 4) as median_similarity,
    ROUND(bs.min_similarity, 4) as min_similarity,
    ROUND(bs.max_similarity, 4) as max_similarity,
    
    -- PRECISION PERCENTAGES (Higher = Better)
    ROUND(qd.excellent_records * 100.0 / qd.total_for_pct, 2) as excellent_precision_pct,
    ROUND((qd.excellent_records + qd.very_good_records) * 100.0 / qd.total_for_pct, 2) as very_good_plus_pct,
    ROUND((qd.excellent_records + qd.very_good_records + qd.good_records) * 100.0 / qd.total_for_pct, 2) as acceptable_precision_pct,
    ROUND(qd.poor_records * 100.0 / qd.total_for_pct, 2) as poor_precision_pct,
    
    -- CLUSTER QUALITY METRICS
    ROUND(ca.avg_cluster_size, 2) as avg_cluster_size,
    ROUND(ca.cluster_size_variance, 2) as cluster_size_consistency,
    ca.min_cluster_size,
    ca.max_cluster_size,
    ROUND(ca.avg_${id_col}s_per_cluster, 2) as avg_${id_col}s_per_cluster,
    ROUND(ca.pure_clusters * 100.0 / ca.total_clusters, 2) as cluster_purity_pct,
    ROUND(ca.avg_intra_cluster_similarity, 4) as avg_intra_cluster_similarity,
    
    -- RECORD DISTRIBUTION
    CAST(qd.excellent_records AS BIGINT) as excellent_records,
    CAST(qd.very_good_records AS BIGINT) as very_good_records,
    CAST(qd.good_records AS BIGINT) as good_records,
    CAST(qd.fair_records AS BIGINT) as fair_records,
    CAST(qd.poor_records AS BIGINT) as poor_records,
    
    -- KEY PERFORMANCE INDICATORS (KPIs) for Easy Comparison
    CASE 
        WHEN bs.avg_similarity_score >= 0.95 THEN 'Excellent'
        WHEN bs.avg_similarity_score >= 0.90 THEN 'Very Good'
        WHEN bs.avg_similarity_score >= 0.85 THEN 'Good'
        WHEN bs.avg_similarity_score >= 0.80 THEN 'Fair'
        ELSE 'Needs Improvement'
    END as overall_quality_rating,
    
    CASE 
        WHEN (qd.excellent_records + qd.very_good_records) * 100.0 / qd.total_for_pct >= 80 THEN 'High Precision'
        WHEN (qd.excellent_records + qd.very_good_records + qd.good_records) * 100.0 / qd.total_for_pct >= 70 THEN 'Good Precision'
        ELSE 'Low Precision'
    END as precision_rating,
    
    
    -- EFFICIENCY SCORE (Composite metric for ranking configurations)
    ROUND(
        (bs.avg_similarity_score * 0.4) + 
        ((qd.excellent_records + qd.very_good_records) / qd.total_for_pct * 0.3) +
        (ca.pure_clusters / ca.total_clusters * 0.2) +
        (LEAST(bs.total_records / bs.unique_${id_col}s / 10, 1.0) * 0.1), 4
    ) as composite_efficiency_score

FROM base_stats bs
CROSS JOIN quality_distribution qd
CROSS JOIN cluster_analysis ca;