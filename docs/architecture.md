# System Architecture & Technical Specifications
## Forest Cover Type Prediction & Wildfire-Risk Analysis

---

## 1. High-Level System Architecture

```
+-----------------------------------------------------------------------------------------+
|                                    DATA SOURCE LAYER                                     |
|  - data/raw/covtype.csv (581,012 rows × 55 columns, Read-Only, SHA-256 Verified)         |
|  - data/external/forestfires.csv (517 rows, UCI Forest Fires Dataset)                    |
+-----------------------------------------------------------------------------------------+
                                           |
                                           v
+-----------------------------------------------------------------------------------------+
|                                 PYTHON PIPELINE CORE                                    |
|  - python_src/ingestion.py        : Ingestion, schema typing, manifest tracking          |
|  - python_src/cleaning.py         : IQR/Z-score outlier flags, quality auditing          |
|  - python_src/synthetic_data.py   : Controlled 800-cell synthetic cleaning demo          |
|  - python_src/statistics.py       : Pearson correlation, Chi-square testing              |
|  - python_src/preprocessing.py    : Stratified split, Gaussian smoothing, scaling, bins  |
|  - python_src/dimensionality_reduction.py: PCA decomposition & loadings analysis        |
|  - python_src/classification.py   : Decision Tree, Random Forest, KNN models             |
|  - python_src/clustering.py       : K-Means (k=7) & Agglomerative clustering             |
|  - python_src/regression.py       : Forest Fires burned area regression (log1p)          |
|  - python_src/visualization.py    : 18+ Matplotlib/Seaborn publication plots             |
|  - python_src/exports.py          : Multi-platform integration pipelines                 |
+-----------------------------------------------------------------------------------------+
           |                               |                                |
           v                               v                                v
+----------------------+       +-----------------------+       +--------------------------+
|  KNIME INTEGRATION   |       |  TABLEAU INTEGRATION  |       |   POSTGRESQL DATABASE    |
|  - exports/knime/*.csv       |  - exports/tableau/*.csv      |  - raw.ingestion_log     |
|  - 6 Executable Workflows    |  - Dashboards 1, 2, 3         |  - curated.forest_cover  |
|  - Comparative Protocols     |  - Calculated Fields          |  - analytics.v_* views   |
+----------------------+       +-----------------------+       +--------------------------+
                                                                            |
                                                                            v
                                                       +----------------------------------+
                                                       |         FULL-STACK APP           |
                                                       |  - backend/: FastAPI REST API    |
                                                       |  - frontend/: Next.js TypeScript |
                                                       +----------------------------------+
```

---

## 2. PostgreSQL Multi-Schema Design

The database maintains strict separation of concerns across 4 schemas:

1. **`raw`**:
   - `raw.ingestion_log`: Stores immutable records of data loads including source file paths, SHA-256 digests, row counts, and loading timestamps.
2. **`curated`**:
   - `curated.forest_cover`: Validated, typed records with single-source-of-truth column naming, indexed on `cover_type`, `elevation`, and `wilderness_area_name`.
3. **`analytics`**:
   - `analytics.model_registry`: Machine learning model artifacts, hyperparameters, and cross-validation performance.
   - `analytics.cluster_profiles`: Mean centroid feature vectors.
   - Views:
     - `v_cover_type_summary`: Class distribution, percentages, terrain averages.
     - `v_terrain_profile`: Multidimensional topographic cross-sections.
     - `v_wildfire_screening_risk`: Topographic screening score based on proximity, slope, and solar exposure.
4. **`app`**:
   - `app.prediction_requests`: High-speed request logging for real-time model inferences.

---

## 3. Data Integrity & Anti-Leakage Safeguards

1. **Source Immutability**: `data/raw/covtype.csv` is read-only. Scripts check SHA-256 digests before execution.
2. **Strict Stratified Splitting**: 80/20 train/test split partitions records before any feature transformation. Split indices are saved to disk (`models/split_indices.json`).
3. **Fit-Transform Boundary**: All scalers, imputers, and PCA transformers are fitted *exclusively* on the training set (`X_train`) and only applied (`transform()`) to the test set (`X_test`).
4. **Id Exclusions**: `record_id` is never used as an input feature for ML models.
5. **Deterministic Random Seeds**: Standardized seed (`42`) ensures exact reproducibility across Python, KNIME, and database sampling.
