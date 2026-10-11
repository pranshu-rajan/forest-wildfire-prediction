-- ============================================================================
-- Forest Cover Type & Wildfire-Risk Analysis Database Schema
-- Multi-Schema Architecture: raw, curated, analytics, app
-- ============================================================================

-- Create schemas
CREATE SCHEMA IF NOT EXISTS raw;
CREATE SCHEMA IF NOT EXISTS curated;
CREATE SCHEMA IF NOT EXISTS analytics;
CREATE SCHEMA IF NOT EXISTS app;

-- ----------------------------------------------------------------------------
-- 1. Metadata and Ingestion Tracking (raw schema)
-- ----------------------------------------------------------------------------
CREATE TABLE IF NOT EXISTS raw.ingestion_log (
    id SERIAL PRIMARY KEY,
    dataset_name VARCHAR(100) NOT NULL,
    dataset_version VARCHAR(50) NOT NULL,
    source_file_path TEXT NOT NULL,
    sha256_hash VARCHAR(64) NOT NULL,
    row_count INT NOT NULL,
    column_count INT NOT NULL,
    loaded_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    status VARCHAR(20) NOT NULL DEFAULT 'SUCCESS',
    notes TEXT
);

-- ----------------------------------------------------------------------------
-- 2. Curated Forest Cover Type Records (curated schema)
-- ----------------------------------------------------------------------------
CREATE TABLE IF NOT EXISTS curated.forest_cover (
    record_id SERIAL PRIMARY KEY,
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
    wilderness_area_1 SMALLINT NOT NULL,
    wilderness_area_2 SMALLINT NOT NULL,
    wilderness_area_3 SMALLINT NOT NULL,
    wilderness_area_4 SMALLINT NOT NULL,
    wilderness_area_name VARCHAR(50),
    cover_type SMALLINT NOT NULL,
    cover_type_name VARCHAR(50) NOT NULL,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP
);

-- Indexes on key analytical and filter columns
CREATE INDEX IF NOT EXISTS idx_fc_cover_type ON curated.forest_cover(cover_type);
CREATE INDEX IF NOT EXISTS idx_fc_elevation ON curated.forest_cover(elevation);
CREATE INDEX IF NOT EXISTS idx_fc_wilderness ON curated.forest_cover(wilderness_area_name);
CREATE INDEX IF NOT EXISTS idx_fc_fire_dist ON curated.forest_cover(horizontal_distance_to_fire_points);

-- ----------------------------------------------------------------------------
-- 3. Model Registries & Metrics (analytics schema)
-- ----------------------------------------------------------------------------
CREATE TABLE IF NOT EXISTS analytics.model_registry (
    model_id SERIAL PRIMARY KEY,
    model_name VARCHAR(100) NOT NULL,
    model_family VARCHAR(50) NOT NULL,
    task_type VARCHAR(50) NOT NULL, -- 'classification' | 'clustering' | 'regression'
    accuracy NUMERIC(6, 4),
    balanced_accuracy NUMERIC(6, 4),
    macro_f1 NUMERIC(6, 4),
    weighted_f1 NUMERIC(6, 4),
    cv_mean NUMERIC(6, 4),
    cv_std NUMERIC(6, 4),
    hyperparameters JSONB,
    artifact_path TEXT,
    trained_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP
);

CREATE TABLE IF NOT EXISTS analytics.cluster_profiles (
    cluster_id INT PRIMARY KEY,
    cluster_size INT NOT NULL,
    mean_elevation NUMERIC(8, 2),
    mean_aspect NUMERIC(8, 2),
    mean_slope NUMERIC(8, 2),
    mean_dist_hydrology NUMERIC(8, 2),
    mean_dist_roadways NUMERIC(8, 2),
    mean_dist_fire_points NUMERIC(8, 2),
    dominant_cover_type VARCHAR(50),
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP
);

-- ----------------------------------------------------------------------------
-- 4. Application Inference Log (app schema)
-- ----------------------------------------------------------------------------
CREATE TABLE IF NOT EXISTS app.prediction_requests (
    request_id UUID PRIMARY KEY,
    elevation INT NOT NULL,
    slope INT NOT NULL,
    aspect INT NOT NULL,
    horizontal_distance_to_roadways INT NOT NULL,
    horizontal_distance_to_fire_points INT NOT NULL,
    predicted_cover_type INT NOT NULL,
    predicted_cover_name VARCHAR(50) NOT NULL,
    confidence NUMERIC(6, 4),
    client_ip VARCHAR(45),
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP
);
