-- ============================================================================
-- Supabase Schema Migration: Forest Cover Type & Wildfire-Risk Analysis
-- Optimized for Supabase PostgreSQL, Connection Pooling & PostgREST API
-- ============================================================================

-- Enable essential extensions
CREATE EXTENSION IF NOT EXISTS "uuid-ossp";
CREATE EXTENSION IF NOT EXISTS "pgcrypto";

-- Create functional schema isolation
CREATE SCHEMA IF NOT EXISTS raw;
CREATE SCHEMA IF NOT EXISTS curated;
CREATE SCHEMA IF NOT EXISTS analytics;
CREATE SCHEMA IF NOT EXISTS models;
CREATE SCHEMA IF NOT EXISTS app;

-- ----------------------------------------------------------------------------
-- 1. Raw Ingestion & Manifests
-- ----------------------------------------------------------------------------
CREATE TABLE IF NOT EXISTS raw.source_manifests (
    id BIGSERIAL PRIMARY KEY,
    dataset_name VARCHAR(100) NOT NULL,
    dataset_version VARCHAR(50) NOT NULL,
    source_file_path TEXT NOT NULL,
    sha256_hash VARCHAR(64) NOT NULL,
    row_count INT NOT NULL,
    column_count INT NOT NULL,
    loaded_at TIMESTAMPTZ DEFAULT NOW(),
    status VARCHAR(20) NOT NULL DEFAULT 'SUCCESS',
    notes TEXT
);

-- ----------------------------------------------------------------------------
-- 2. Curated Forest Cover Type (Validated Features + Outlier Flags)
-- ----------------------------------------------------------------------------
CREATE TABLE IF NOT EXISTS curated.forest_cover (
    record_id BIGSERIAL PRIMARY KEY,
    elevation INT NOT NULL,
    aspect INT NOT NULL,
    slope INT NOT NULL,
    horizontal_distance_to_hydrology INT NOT NULL,
    vertical_distance_to_hydrology INT NOT NULL,
    horizontal_distance_to_roadways INT NOT NULL,
    hillshade_9am INT NOT NULL,
    hillshade_noon INT NOT NULL,
    hillshade_3pm INT NOT NULL,
    horizontal_distance_to_fire_points INT NOT NULL,
    wilderness_area_1 SMALLINT NOT NULL DEFAULT 0,
    wilderness_area_2 SMALLINT NOT NULL DEFAULT 0,
    wilderness_area_3 SMALLINT NOT NULL DEFAULT 0,
    wilderness_area_4 SMALLINT NOT NULL DEFAULT 0,
    wilderness_area_name VARCHAR(50),
    cover_type SMALLINT NOT NULL,
    cover_type_name VARCHAR(50) NOT NULL,
    is_iqr_outlier BOOLEAN DEFAULT FALSE,
    is_zscore_outlier BOOLEAN DEFAULT FALSE,
    created_at TIMESTAMPTZ DEFAULT NOW()
);

CREATE INDEX IF NOT EXISTS idx_fc_cover_type ON curated.forest_cover(cover_type);
CREATE INDEX IF NOT EXISTS idx_fc_elevation ON curated.forest_cover(elevation);
CREATE INDEX IF NOT EXISTS idx_fc_wilderness ON curated.forest_cover(wilderness_area_name);
CREATE INDEX IF NOT EXISTS idx_fc_fire_dist ON curated.forest_cover(horizontal_distance_to_fire_points);

-- ----------------------------------------------------------------------------
-- 3. Analytics Schemas: Statistics, Models, Clusters & Regression
-- ----------------------------------------------------------------------------
CREATE TABLE IF NOT EXISTS analytics.descriptive_statistics (
    id SERIAL PRIMARY KEY,
    feature_name VARCHAR(100) NOT NULL UNIQUE,
    count BIGINT NOT NULL,
    mean NUMERIC(12, 4) NOT NULL,
    std NUMERIC(12, 4) NOT NULL,
    min_val NUMERIC(12, 4) NOT NULL,
    q25 NUMERIC(12, 4) NOT NULL,
    median NUMERIC(12, 4) NOT NULL,
    q75 NUMERIC(12, 4) NOT NULL,
    max_val NUMERIC(12, 4) NOT NULL,
    skewness NUMERIC(8, 4),
    kurtosis NUMERIC(8, 4),
    updated_at TIMESTAMPTZ DEFAULT NOW()
);

CREATE TABLE IF NOT EXISTS analytics.pca_loadings (
    id SERIAL PRIMARY KEY,
    component_name VARCHAR(20) NOT NULL,
    feature_name VARCHAR(100) NOT NULL,
    loading_weight NUMERIC(8, 5) NOT NULL,
    explained_variance_ratio NUMERIC(8, 5) NOT NULL,
    cumulative_variance NUMERIC(8, 5) NOT NULL,
    updated_at TIMESTAMPTZ DEFAULT NOW()
);

CREATE TABLE IF NOT EXISTS analytics.cluster_profiles (
    cluster_id INT PRIMARY KEY,
    cluster_label VARCHAR(100) NOT NULL,
    cluster_size INT NOT NULL,
    mean_elevation NUMERIC(8, 2),
    mean_aspect NUMERIC(8, 2),
    mean_slope NUMERIC(8, 2),
    mean_dist_hydrology NUMERIC(8, 2),
    mean_dist_roadways NUMERIC(8, 2),
    mean_dist_fire_points NUMERIC(8, 2),
    dominant_cover_type VARCHAR(50),
    updated_at TIMESTAMPTZ DEFAULT NOW()
);

CREATE TABLE IF NOT EXISTS models.model_registry (
    model_id SERIAL PRIMARY KEY,
    model_name VARCHAR(100) NOT NULL UNIQUE,
    model_family VARCHAR(50) NOT NULL,
    task_type VARCHAR(50) NOT NULL, -- classification | clustering | regression
    accuracy NUMERIC(6, 4),
    macro_f1 NUMERIC(6, 4),
    weighted_f1 NUMERIC(6, 4),
    cv_mean NUMERIC(6, 4),
    cv_std NUMERIC(6, 4),
    hyperparameters JSONB,
    artifact_path TEXT,
    trained_at TIMESTAMPTZ DEFAULT NOW()
);

CREATE TABLE IF NOT EXISTS analytics.regression_benchmarks (
    id SERIAL PRIMARY KEY,
    benchmark_name VARCHAR(100) NOT NULL,
    target_variable VARCHAR(50) NOT NULL,
    model_name VARCHAR(50) NOT NULL,
    rmse NUMERIC(8, 4) NOT NULL,
    mae NUMERIC(8, 4) NOT NULL,
    r2_score NUMERIC(8, 4) NOT NULL,
    evaluated_at TIMESTAMPTZ DEFAULT NOW()
);

-- ----------------------------------------------------------------------------
-- 4. Application Schema: Inference & Screening
-- ----------------------------------------------------------------------------
CREATE TABLE IF NOT EXISTS app.prediction_requests (
    request_id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    model_used VARCHAR(50) NOT NULL,
    elevation INT NOT NULL,
    aspect INT NOT NULL,
    slope INT NOT NULL,
    horizontal_distance_to_roadways INT NOT NULL,
    horizontal_distance_to_fire_points INT NOT NULL,
    wilderness_area_name VARCHAR(50),
    predicted_cover_type INT NOT NULL,
    predicted_cover_name VARCHAR(50) NOT NULL,
    probabilities JSONB,
    created_at TIMESTAMPTZ DEFAULT NOW()
);

CREATE TABLE IF NOT EXISTS app.wildfire_screening_risk (
    id SERIAL PRIMARY KEY,
    wilderness_area VARCHAR(50) NOT NULL,
    elevation_bracket VARCHAR(50) NOT NULL,
    mean_risk_score NUMERIC(6, 2) NOT NULL,
    risk_level VARCHAR(20) NOT NULL,
    sample_count INT NOT NULL,
    updated_at TIMESTAMPTZ DEFAULT NOW()
);

-- ----------------------------------------------------------------------------
-- 5. Analytical Views for Reporting & Tableau Integration
-- ----------------------------------------------------------------------------
CREATE OR REPLACE VIEW analytics.v_cover_type_summary AS
SELECT
    cover_type,
    cover_type_name,
    COUNT(*) AS total_count,
    ROUND(COUNT(*) * 100.0 / SUM(COUNT(*)) OVER (), 2) AS percentage,
    ROUND(AVG(elevation)::numeric, 1) AS avg_elevation,
    MIN(elevation) AS min_elevation,
    MAX(elevation) AS max_elevation,
    ROUND(AVG(horizontal_distance_to_fire_points)::numeric, 1) AS avg_fire_point_distance
FROM curated.forest_cover
GROUP BY cover_type, cover_type_name;

CREATE OR REPLACE VIEW analytics.v_wildfire_screening_risk AS
SELECT
    wilderness_area_name,
    CASE
        WHEN elevation < 2500 THEN 'Low Elevation (<2500m)'
        WHEN elevation BETWEEN 2500 AND 3000 THEN 'Mid Elevation (2500-3000m)'
        ELSE 'High Elevation (>3000m)'
    END AS elevation_bracket,
    COUNT(*) AS cell_count,
    ROUND(AVG(
        0.40 * (1.0 - LEAST(horizontal_distance_to_fire_points, 5000)::numeric / 5000.0) * 100.0 +
        0.35 * (LEAST(slope, 45)::numeric / 45.0) * 100.0 +
        0.25 * (hillshade_noon::numeric / 254.0) * 100.0
    ), 2) AS mean_screening_risk_score
FROM curated.forest_cover
GROUP BY wilderness_area_name, elevation_bracket;

-- ----------------------------------------------------------------------------
-- 6. Supabase Row Level Security (RLS) Configuration
-- ----------------------------------------------------------------------------
ALTER TABLE curated.forest_cover ENABLE ROW LEVEL SECURITY;
ALTER TABLE analytics.descriptive_statistics ENABLE ROW LEVEL SECURITY;
ALTER TABLE analytics.cluster_profiles ENABLE ROW LEVEL SECURITY;
ALTER TABLE analytics.pca_loadings ENABLE ROW LEVEL SECURITY;
ALTER TABLE models.model_registry ENABLE ROW LEVEL SECURITY;
ALTER TABLE app.prediction_requests ENABLE ROW LEVEL SECURITY;
ALTER TABLE app.wildfire_screening_risk ENABLE ROW LEVEL SECURITY;

-- Allow read-only access for anon role (public dashboard & web app)
DO $$
BEGIN
    DROP POLICY IF EXISTS "Public can view curated cover" ON curated.forest_cover;
    CREATE POLICY "Public can view curated cover" ON curated.forest_cover FOR SELECT USING (true);

    DROP POLICY IF EXISTS "Public can view statistics" ON analytics.descriptive_statistics;
    CREATE POLICY "Public can view statistics" ON analytics.descriptive_statistics FOR SELECT USING (true);

    DROP POLICY IF EXISTS "Public can view clusters" ON analytics.cluster_profiles;
    CREATE POLICY "Public can view clusters" ON analytics.cluster_profiles FOR SELECT USING (true);

    DROP POLICY IF EXISTS "Public can view models" ON models.model_registry;
    CREATE POLICY "Public can view models" ON models.model_registry FOR SELECT USING (true);

    DROP POLICY IF EXISTS "Public can insert predictions" ON app.prediction_requests;
    CREATE POLICY "Public can insert predictions" ON app.prediction_requests FOR INSERT WITH CHECK (true);
EXCEPTION WHEN OTHERS THEN
    -- In environments without Supabase roles, continue cleanly
    NULL;
END $$;
