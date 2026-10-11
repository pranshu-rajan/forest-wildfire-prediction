# Canonical Schema Registry & Integration Contracts

## Forest Cover Type Prediction & Wildfire-Risk Analysis
**Multi-Platform Schema Specifications: Python ↔ Supabase ↔ KNIME ↔ Tableau ↔ FastAPI ↔ Next.js**

---

## 1. Master Architectural Principles & Data Integrity Rules

1. **Immutable Raw Truth**: The source dataset (`data/raw/covtype.csv`) retains its verified SHA-256 fingerprint (`b6e4e...`). It is strictly read-only and never modified.
2. **Predictive Boundary & Feature Exclusions**:
   - Exactly **54 environmental predictors** are admitted into predictive model pipelines (10 continuous, 4 wilderness binary, 40 soil binary).
   - Any surrogate ID (e.g. `record_id`, `observation_id`, row numbers) or synthetic metadata generated for database tracking is strictly excluded from feature vectors to prevent data leakage.
   - The target variable `Cover_Type` is strictly integer-coded $[1, 7]$.
3. **Missing Value Invariants**:
   - Curated operational dataset contains **0 missing cells**.
   - Synthetic educational demo dataset (`data/processed/covtype_missing_values_demo.csv`) contains **exactly 800 injected nulls** across continuous features in 10,000 sampled rows, resolved via median imputation.
4. **Lineage Metadata**:
   - Every analytical table and JSON response contains `dataset_version` (`v1.0.0`), `schema_version` (`v1.0.0`), `pipeline_run_id`, and ISO-8601 UTC `generated_at` timestamp.

---

## 2. Canonical Feature Dictionary & Unit Registry

### Continuous Predictors (10 Features)

| Feature Name | Storage Type | Physical Unit | Valid Domain | Missing Behavior | Description |
| :--- | :--- | :--- | :--- | :--- | :--- |
| `Elevation` | Float / Double | Meters | $[1859, 3858]$ | Zero missing; median fallback | Elevation above sea level |
| `Aspect` | Float / Double | Degrees (Azimuth) | $[0, 360]$ | Zero missing; median fallback | Aspect in degrees azimuth |
| `Slope` | Float / Double | Degrees | $[0, 66]$ | Zero missing; median fallback | Slope angle in degrees |
| `Horizontal_Distance_To_Hydrology` | Float / Double | Meters | $[0, 1397]$ | Zero missing; median fallback | Horizontal distance to nearest water surface |
| `Vertical_Distance_To_Hydrology` | Float / Double | Meters | $[-173, 601]$ | Zero missing; median fallback | Vertical distance to nearest surface water |
| `Horizontal_Distance_To_Roadways` | Float / Double | Meters | $[0, 7117]$ | Zero missing; median fallback | Horizontal distance to nearest road |
| `Hillshade_9am` | Float / Double | Index $(0–255)$ | $[0, 254]$ | Zero missing; median fallback | Hillshade index at 9am, summer solstice |
| `Hillshade_Noon` | Float / Double | Index $(0–255)$ | $[0, 254]$ | Zero missing; median fallback | Hillshade index at noon, summer solstice |
| `Hillshade_3pm` | Float / Double | Index $(0–255)$ | $[0, 254]$ | Zero missing; median fallback | Hillshade index at 3pm, summer solstice |
| `Horizontal_Distance_To_Fire_Points` | Float / Double | Meters | $[0, 7173]$ | Zero missing; median fallback | Horizontal distance to nearest historic fire ignition point |

### Categorical & Binary Indicators (44 Features)

| Group | Field Pattern | Storage Type | Domain | Description |
| :--- | :--- | :--- | :--- | :--- |
| Wilderness Area (4) | `Wilderness_Area1` to `Wilderness_Area4` | Integer (0/1) | $\{0, 1\}$ | Mutually exclusive binary designation (Rawah, Neota, Comanche Peak, Cache la Poudre) |
| Soil Type (40) | `Soil_Type1` to `Soil_Type40` | Integer (0/1) | $\{0, 1\}$ | One-hot binary soil geological family designation |

### Target Variable (1 Feature)

| Target Name | Storage Type | Class Domain | Label Mapping |
| :--- | :--- | :--- | :--- |
| `Cover_Type` | Integer (1–7) | $\{1, 2, 3, 4, 5, 6, 7\}$ | 1: Spruce/Fir, 2: Lodgepole Pine, 3: Ponderosa Pine, 4: Cottonwood/Willow, 5: Aspen, 6: Douglas-fir, 7: Krummholz |

---

## 3. Technology-Specific Integration Contracts

### Contract A: Python ↔ Supabase (Managed PostgreSQL)
- **Engine Protocol**: Direct PostgreSQL via SQLAlchemy + `psycopg3` (connection pooling enabled) OR Supabase Python Client via REST API.
- **Environment Variables**:
  - `SUPABASE_URL`: e.g. `https://xyzproject.supabase.co`
  - `SUPABASE_KEY`: Supabase service_role or anon key.
  - `DATABASE_URL`: Connection string `postgresql+psycopg://postgres.[ref]:[password]@aws-0-[region].pooler.supabase.com:6543/postgres`
- **Schemas**:
  1. `raw.source_manifests`: Ingestion logs, cryptographic hashes, row/col counts.
  2. `curated.covtype_clean`: Preprocessed 581,012 records with outlier flags (`is_iqr_outlier`, `is_zscore_outlier`).
  3. `analytics.*`:
     - `descriptive_statistics`: 5-number summary, mean, std, skewness per feature.
     - `feature_rankings`: Chi-Square scores, ANOVA F-values, Pearson correlations.
     - `pca_loadings`: Eigenvectors, eigenvalues, and explained variance ratios.
     - `cluster_profiles`: Centroid coordinates for $k=4$ K-Means clusters.
     - `classification_metrics`: Precision, recall, macro F1, test accuracy per model.
     - `forest_fires_regression`: RMSE, MAE, $R^2$ on UCI Forest Fires benchmark.
  4. `models.registry`: Model metadata, hyperparameter hashes, serialized artifact locations.
  5. `app.*`:
     - `prediction_logs`: Interactive web predictions (timestamp, features, predicted class, latency).
     - `synthetic_cleaning_demo`: 10,000 synthetic rows (raw with nulls + imputed values).
     - `wildfire_screening_aggregates`: Precomputed topographic risk screening indices.

---

### Contract B: Python ↔ KNIME Analytics Platform
- **Format**: Headless-compatible, RFC-4180 compliant CSV exports located in `exports/knime/`.
- **Export Registry**:
  1. `exports/knime/covtype_curated_sample.csv` (20,000 rows × 55 columns for visual processing).
  2. `exports/knime/covtype_missing_experiment.csv` (10,000 rows with exactly 800 missing cells for Practical 2).
  3. `exports/knime/continuous_features_normalized.csv` (MinMax & Z-Score standardizations for Practical 6).
  4. `exports/knime/correlation_matrix.csv` (Pairwise Pearson matrix).
  5. `exports/knime/pca_projected_sample.csv` (8 PC projections + Target for Practical 6b).
  6. `exports/knime/train_test_split_info.csv` (Stratified train/val/test row indexes).
  7. `exports/knime/cluster_assignments.csv` (Cluster IDs 0–3 mapped to spatial features).
  8. `exports/knime/forest_fires_curated.csv` (UCI Forest Fires data for Practical 9).
  9. `exports/knime/data_dictionary.csv` (Canonical feature definitions).
  10. `exports/knime/class_distribution.csv` (Class frequency table).

---

### Contract C: Python / Supabase ↔ Tableau Desktop / Server
- **Format**: PostgreSQL live views / curated extracts located in `exports/tableau/`.
- **Views & Sources**:
  1. `v_cover_type_summary` (`exports/tableau/tableau_cover_type_summary.csv`): Class distribution, elevation envelope, water proximity.
  2. `v_terrain_profile` (`exports/tableau/tableau_terrain_profile.csv`): 10,000-row representative slice with Aspect degrees, Slope, Hillshade.
  3. `v_wildfire_screening_risk` (`exports/tableau/wildfire_screening_aggregates.csv`): Aggregated risk strata by Wilderness Area and Elevation bracket.
  4. `tableau_correlation_matrix.csv`: Flattened pairwise correlation table `(Feature_A, Feature_B, Pearson_R)`.
  5. `tableau_model_comparison.csv`: Model metrics (Random Forest, Decision Tree, KNN).
  6. `tableau_confusion_matrix.csv`: 7×7 normalized confusion matrices.
  7. `tableau_cluster_summary.csv`: Cluster centroids with natural-language terrain descriptions.

---

### Contract D: FastAPI Backend ↔ Next.js Web Frontend
- **Format**: JSON over HTTP, strict Pydantic schemas, CORS enabled.
- **REST Contract Endpoints**:
  - `GET /health`: `{ status: "OK", database: { status: "OK"|"STANDALONE_MODE" }, models_available: string[] }`
  - `GET /api/dataset/summary`: `{ dataset_name: string, total_rows: 581012, total_columns: 55, continuous_features_count: 10, ... }`
  - `GET /api/dataset/distribution`: `[{ Cover_Type: 1, cover_name: "Spruce/Fir", count: 211840, pct: 36.46 }, ...]`
  - `GET /api/dataset/features`: `[{ column: string, type: "Continuous"|"Binary", range: string, description: string }, ...]`
  - `GET /api/data-quality/report`: `{ source_quality: [...], synthetic_cleaning_experiment: { injected_nulls: 800, imputed_nulls: 800, ... } }`
  - `GET /api/statistics/descriptive`: `[{ feature: string, count: int, mean: float, std: float, min: float, q25: float, median: float, q75: float, max: float, skewness: float }, ...]`
  - `GET /api/features/pca-analysis`: `{ cumulative_variance: float, components_retained: 8, loadings: [...], scree: [...] }`
  - `GET /api/models/metrics`: `{ models: [{ name: "random_forest", accuracy: 0.935, macro_f1: 0.906, ... }], confusion_matrix: [...] }`
  - `GET /api/clusters/summary`: `{ profiles: [...], evaluation: [{ k: 2, inertia: ..., silhouette: ... }, ...] }`
  - `GET /api/regression/metrics`: `{ dataset: "UCI Forest Fires", target: "log1p(area)", models: [{ model: "RandomForestRegressor", rmse: ..., mae: ..., r2: ... }] }`
  - `POST /api/predict`:
    - **Request**: `{ features: { Elevation: 2950, Aspect: 120, ... }, model: "random_forest" }`
    - **Response**: `{ predicted_cover_type: 2, cover_name: "Lodgepole Pine", probabilities: { "Lodgepole Pine": 0.88, ... }, model_used: "random_forest", timestamp: "..." }`
  - `GET /api/wildfire-screening/summary`: `{ methodology: { formula: "...", limitations: [...] }, aggregates: [...] }`
