-- Enhanced search analytics table for vector search tracking
-- This migration extends the search analytics to capture vector search performance metrics

-- Drop existing search_analytics table if it exists and recreate with enhanced schema
DROP TABLE IF EXISTS public.search_analytics CASCADE;

CREATE TABLE public.search_analytics (
    id BIGSERIAL PRIMARY KEY,
    
    -- Query details
    query TEXT NOT NULL,
    strategy TEXT DEFAULT 'hybrid' CHECK (strategy IN ('semantic', 'combined', 'hybrid')),
    filters JSONB DEFAULT '{}',
    
    -- Search parameters
    similarity_threshold DECIMAL(3,2) DEFAULT 0.7,
    max_results INTEGER DEFAULT 20,
    page INTEGER DEFAULT 1,
    
    -- Results metrics
    results_count INTEGER NOT NULL DEFAULT 0,
    total_results INTEGER DEFAULT 0,
    
    -- Performance metrics
    embedding_generated BOOLEAN DEFAULT false,
    fallback_used BOOLEAN DEFAULT false,
    embedding_time_ms INTEGER DEFAULT 0,
    search_time_ms INTEGER DEFAULT 0,
    total_time_ms INTEGER DEFAULT 0,
    cache_hit BOOLEAN DEFAULT false,
    
    -- Client information
    client_ip TEXT,
    user_agent TEXT,
    
    -- Legacy fields for backward compatibility
    extracted_criteria JSONB DEFAULT '{}',
    openai_used BOOLEAN DEFAULT false,
    
    -- Timestamps
    created_at TIMESTAMPTZ DEFAULT timezone('utc'::text, now()) NOT NULL,
    
    -- Add constraints
    CONSTRAINT valid_similarity_threshold CHECK (similarity_threshold >= 0 AND similarity_threshold <= 1),
    CONSTRAINT valid_results_count CHECK (results_count >= 0),
    CONSTRAINT valid_performance_metrics CHECK (
        embedding_time_ms >= 0 AND 
        search_time_ms >= 0 AND 
        total_time_ms >= 0
    )
);

-- Create indexes for analytics queries
CREATE INDEX idx_search_analytics_created_at ON public.search_analytics(created_at);
CREATE INDEX idx_search_analytics_query ON public.search_analytics USING gin(to_tsvector('english', query));
CREATE INDEX idx_search_analytics_strategy ON public.search_analytics(strategy);
CREATE INDEX idx_search_analytics_results_count ON public.search_analytics(results_count);
CREATE INDEX idx_search_analytics_performance ON public.search_analytics(total_time_ms, embedding_time_ms, search_time_ms);
CREATE INDEX idx_search_analytics_client_stats ON public.search_analytics(client_ip, created_at);

-- GIN index for filters JSONB field
CREATE INDEX idx_search_analytics_filters ON public.search_analytics USING gin(filters);

-- Create a materialized view for search performance analytics
CREATE MATERIALIZED VIEW public.search_performance_summary AS
SELECT 
    DATE_TRUNC('hour', created_at) as hour,
    strategy,
    COUNT(*) as query_count,
    AVG(results_count) as avg_results,
    AVG(total_time_ms) as avg_total_time_ms,
    AVG(embedding_time_ms) as avg_embedding_time_ms,
    AVG(search_time_ms) as avg_search_time_ms,
    COUNT(*) FILTER (WHERE embedding_generated = true) as embedding_queries,
    COUNT(*) FILTER (WHERE fallback_used = true) as fallback_queries,
    COUNT(*) FILTER (WHERE cache_hit = true) as cache_hits,
    COUNT(*) FILTER (WHERE results_count = 0) as zero_result_queries,
    PERCENTILE_CONT(0.95) WITHIN GROUP (ORDER BY total_time_ms) as p95_total_time_ms
FROM public.search_analytics
WHERE created_at >= NOW() - INTERVAL '7 days'
GROUP BY DATE_TRUNC('hour', created_at), strategy
ORDER BY hour DESC, strategy;

-- Create unique index on materialized view
CREATE UNIQUE INDEX idx_search_performance_summary_unique 
    ON public.search_performance_summary(hour, strategy);

-- Create a view for popular search queries
CREATE VIEW public.popular_searches AS
SELECT 
    query,
    strategy,
    COUNT(*) as search_count,
    AVG(results_count) as avg_results,
    AVG(total_time_ms) as avg_time_ms,
    COUNT(*) FILTER (WHERE results_count > 0) as successful_searches,
    MAX(created_at) as last_searched
FROM public.search_analytics
WHERE created_at >= NOW() - INTERVAL '30 days'
GROUP BY query, strategy
HAVING COUNT(*) >= 2  -- Only show queries searched at least twice
ORDER BY search_count DESC, avg_results DESC;

-- Create a function to refresh the materialized view
CREATE OR REPLACE FUNCTION refresh_search_performance_summary()
RETURNS void AS $$
BEGIN
    REFRESH MATERIALIZED VIEW CONCURRENTLY public.search_performance_summary;
END;
$$ LANGUAGE plpgsql;

-- Create a function to clean old analytics data (older than 90 days)
CREATE OR REPLACE FUNCTION cleanup_old_search_analytics()
RETURNS INTEGER AS $$
DECLARE
    deleted_count INTEGER;
BEGIN
    DELETE FROM public.search_analytics 
    WHERE created_at < NOW() - INTERVAL '90 days';
    
    GET DIAGNOSTICS deleted_count = ROW_COUNT;
    
    -- Refresh the materialized view after cleanup
    PERFORM refresh_search_performance_summary();
    
    RETURN deleted_count;
END;
$$ LANGUAGE plpgsql;

-- Create a function to get search insights
CREATE OR REPLACE FUNCTION get_search_insights(
    hours_back INTEGER DEFAULT 24
)
RETURNS TABLE (
    metric TEXT,
    value NUMERIC,
    change_percent NUMERIC
) AS $$
BEGIN
    RETURN QUERY
    WITH current_period AS (
        SELECT 
            COUNT(*) as total_queries,
            AVG(total_time_ms) as avg_time,
            COUNT(*) FILTER (WHERE results_count > 0) as successful_queries,
            COUNT(*) FILTER (WHERE fallback_used = true) as fallback_queries,
            COUNT(*) FILTER (WHERE cache_hit = true) as cache_queries
        FROM public.search_analytics
        WHERE created_at >= NOW() - (hours_back || ' hours')::INTERVAL
    ),
    previous_period AS (
        SELECT 
            COUNT(*) as total_queries,
            AVG(total_time_ms) as avg_time,
            COUNT(*) FILTER (WHERE results_count > 0) as successful_queries,
            COUNT(*) FILTER (WHERE fallback_used = true) as fallback_queries,
            COUNT(*) FILTER (WHERE cache_hit = true) as cache_queries
        FROM public.search_analytics
        WHERE created_at >= NOW() - (hours_back * 2 || ' hours')::INTERVAL
            AND created_at < NOW() - (hours_back || ' hours')::INTERVAL
    )
    SELECT 'Total Queries'::TEXT, 
           c.total_queries::NUMERIC,
           CASE WHEN p.total_queries > 0 
                THEN ((c.total_queries - p.total_queries) * 100.0 / p.total_queries)
                ELSE 0 END
    FROM current_period c, previous_period p
    
    UNION ALL
    
    SELECT 'Avg Response Time (ms)'::TEXT,
           ROUND(c.avg_time, 2),
           CASE WHEN p.avg_time > 0 
                THEN ROUND(((c.avg_time - p.avg_time) * 100.0 / p.avg_time), 2)
                ELSE 0 END
    FROM current_period c, previous_period p
    
    UNION ALL
    
    SELECT 'Success Rate (%)'::TEXT,
           ROUND((c.successful_queries * 100.0 / NULLIF(c.total_queries, 0)), 2),
           CASE WHEN p.total_queries > 0 AND c.total_queries > 0
                THEN ROUND((
                    (c.successful_queries * 100.0 / c.total_queries) - 
                    (p.successful_queries * 100.0 / p.total_queries)
                ), 2)
                ELSE 0 END
    FROM current_period c, previous_period p
    
    UNION ALL
    
    SELECT 'Cache Hit Rate (%)'::TEXT,
           ROUND((c.cache_queries * 100.0 / NULLIF(c.total_queries, 0)), 2),
           CASE WHEN p.total_queries > 0 AND c.total_queries > 0
                THEN ROUND((
                    (c.cache_queries * 100.0 / c.total_queries) - 
                    (p.cache_queries * 100.0 / p.total_queries)
                ), 2)
                ELSE 0 END
    FROM current_period c, previous_period p;
END;
$$ LANGUAGE plpgsql;

-- Enable Row Level Security
ALTER TABLE public.search_analytics ENABLE ROW LEVEL SECURITY;

-- Create RLS policies
CREATE POLICY "Search analytics are viewable by authenticated users" ON public.search_analytics
    FOR SELECT USING (auth.role() = 'authenticated');

CREATE POLICY "Search analytics can be inserted by anyone" ON public.search_analytics
    FOR INSERT WITH CHECK (true);  -- Allow public inserts for search tracking

-- Create policies for views
ALTER VIEW public.popular_searches OWNER TO postgres;
ALTER MATERIALIZED VIEW public.search_performance_summary OWNER TO postgres;

-- Grant necessary permissions
GRANT SELECT ON public.search_analytics TO anon, authenticated;
GRANT INSERT ON public.search_analytics TO anon, authenticated;
GRANT SELECT ON public.popular_searches TO authenticated;
GRANT SELECT ON public.search_performance_summary TO authenticated;

-- Add helpful comments
COMMENT ON TABLE public.search_analytics IS 'Comprehensive analytics for vector and keyword search performance tracking';
COMMENT ON COLUMN public.search_analytics.strategy IS 'Search strategy used: semantic, combined, or hybrid';
COMMENT ON COLUMN public.search_analytics.filters IS 'JSON object containing applied search filters';
COMMENT ON COLUMN public.search_analytics.embedding_time_ms IS 'Time taken to generate query embedding in milliseconds';
COMMENT ON COLUMN public.search_analytics.search_time_ms IS 'Time taken to execute search query in milliseconds';
COMMENT ON MATERIALIZED VIEW public.search_performance_summary IS 'Hourly aggregated search performance metrics for monitoring and optimization';
COMMENT ON VIEW public.popular_searches IS 'Most frequently searched queries with performance statistics';

-- Schedule materialized view refresh (requires pg_cron extension)
-- This will run every hour to keep the performance summary up to date
-- SELECT cron.schedule('refresh-search-performance', '0 * * * *', 'SELECT refresh_search_performance_summary();');

-- Schedule cleanup of old analytics data (runs daily at 2 AM)
-- SELECT cron.schedule('cleanup-search-analytics', '0 2 * * *', 'SELECT cleanup_old_search_analytics();');