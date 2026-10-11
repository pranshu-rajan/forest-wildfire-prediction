-- ============================================================================
-- Forest Cover Type & Wildfire-Risk Analysis Views
-- Shared analytical views for Tableau, KNIME, and FastAPI
-- ============================================================================

-- 1. Executive Summary View: Class distributions & percentages
CREATE OR REPLACE VIEW analytics.v_cover_type_summary AS
SELECT
    cover_type,
    cover_type_name,
    COUNT(*) AS total_observations,
    ROUND(COUNT(*) * 100.0 / SUM(COUNT(*)) OVER (), 2) AS percentage_of_total,
    ROUND(AVG(elevation), 1) AS mean_elevation,
    ROUND(AVG(slope), 1) AS mean_slope,
    ROUND(AVG(horizontal_distance_to_fire_points), 1) AS mean_distance_to_fire_points
FROM curated.forest_cover
GROUP BY cover_type, cover_type_name
ORDER BY cover_type;

-- 2. Terrain Analysis View: Elevation, slope, hillshade gradients
CREATE OR REPLACE VIEW analytics.v_terrain_profile AS
SELECT
    cover_type_name,
    wilderness_area_name,
    COUNT(*) AS sample_size,
    ROUND(AVG(elevation), 1) AS avg_elevation,
    ROUND(AVG(slope), 1) AS avg_slope,
    ROUND(AVG(aspect), 1) AS avg_aspect,
    ROUND(AVG(hillshade_noon), 1) AS avg_hillshade_noon,
    ROUND(AVG(horizontal_distance_to_roadways), 1) AS avg_distance_roadways,
    ROUND(AVG(horizontal_distance_to_fire_points), 1) AS avg_distance_fire_points
FROM curated.forest_cover
GROUP BY cover_type_name, wilderness_area_name;

-- 3. Wildfire Terrain Risk Screening View:
-- NOTE: This view produces an exploratory topographic screening metric,
-- NOT a calibrated empirical fire recurrence probability.
CREATE OR REPLACE VIEW analytics.v_wildfire_screening_risk AS
SELECT
    record_id,
    cover_type_name,
    wilderness_area_name,
    elevation,
    slope,
    horizontal_distance_to_fire_points,
    -- Screening score: composite of proximity, slope gradient, and solar exposure
    ROUND(
        (
            0.40 * (1.0 - LEAST(horizontal_distance_to_fire_points, 7000)::NUMERIC / 7000.0) +
            0.35 * (LEAST(slope, 60)::NUMERIC / 60.0) +
            0.25 * (LEAST(hillshade_noon, 255)::NUMERIC / 255.0)
        ) * 100.0,
        1
    ) AS screening_risk_score,
    CASE
        WHEN (0.40 * (1.0 - LEAST(horizontal_distance_to_fire_points, 7000)::NUMERIC / 7000.0) +
              0.35 * (LEAST(slope, 60)::NUMERIC / 60.0) +
              0.25 * (LEAST(hillshade_noon, 255)::NUMERIC / 255.0)) * 100.0 >= 65 THEN 'High Screening Risk'
        WHEN (0.40 * (1.0 - LEAST(horizontal_distance_to_fire_points, 7000)::NUMERIC / 7000.0) +
              0.35 * (LEAST(slope, 60)::NUMERIC / 60.0) +
              0.25 * (LEAST(hillshade_noon, 255)::NUMERIC / 255.0)) * 100.0 >= 35 THEN 'Moderate Screening Risk'
        ELSE 'Low Screening Risk'
    END AS screening_risk_tier
FROM curated.forest_cover;
