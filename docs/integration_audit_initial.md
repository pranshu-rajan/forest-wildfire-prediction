# Phase A: Initial End-to-End Integration Audit

**Project:** Forest Cover Type Prediction & Wildfire-Risk Analysis (Roosevelt National Forest)  
**Audit Timestamp:** 2026-10-11T13:51:00+05:30  
**Auditor:** Senior Software Integration & Full-Stack QA Engineer  
**Status Taxonomy:**
- `PRESENT_AND_VERIFIED`: Component exists, code runs, tests pass, inputs/outputs align.
- `PRESENT_BUT_UNVERIFIED`: Component exists in codebase but end-to-end live round-trip execution or application launch has not been verified in the native application.
- `PARTIALLY_IMPLEMENTED`: Files or endpoints exist, but schemas diverge or dependencies are partially wired.
- `MISSING`: Required file, workflow, or endpoint does not exist.
- `BLOCKED_BY_CREDENTIALS`: Requires external cloud or database credentials not present in the current environment.
- `REQUIRES_MANUAL_GUI`: Requires interactive desktop GUI verification (Tableau Public / KNIME Analytics Platform).

---

## 1. Project Inventory & Component Audit

### 1.1 Original Dataset & File Integrity
| Item | File Path | Format & Details | Audit Evidence | Status |
| :--- | :--- | :--- | :--- | :--- |
| **Raw Covertype Source** | [`data/raw/covtype.csv`](file:///c:/Users/pranshu/Desktop/forest-cover-wildfire/data/raw/covtype.csv) | CSV, 75,170,064 bytes (71.69 MB). 581,012 rows × 55 columns (54 predictors + 1 target). | SHA-256: `ea35ca6820fcbe0bdc6707e9ed31e11a9de84f07d88da73b511c737383c271a6`. Cryptographically fingerprinted in [`reports/data_quality/source_manifest.json`](file:///c:/Users/pranshu/Desktop/forest-cover-wildfire/reports/data_quality/source_manifest.json). Zero null cells, zero duplicate rows. | `PRESENT_AND_VERIFIED` |
| **Forest Fires External Data** | [`data/external/forestfires.csv`](file:///c:/Users/pranshu/Desktop/forest-cover-wildfire/data/external/forestfires.csv) | CSV, 25,478 bytes. 517 rows × 13 attributes (UCI Forest Fires dataset). | Read by [`scripts/10_train_fires_regression.py`](file:///c:/Users/pranshu/Desktop/forest-cover-wildfire/scripts/10_train_fires_regression.py) for burned area log1p regression. | `PRESENT_AND_VERIFIED` |
| **Curated Clean Parquet** | [`data/processed/covtype_clean.parquet`](file:///c:/Users/pranshu/Desktop/forest-cover-wildfire/data/processed/covtype_clean.parquet) | Snappy Parquet, 9,856,740 bytes (9.40 MB). 581,012 rows × 56 columns (`record_id` added). | Validated in [`tests/test_ingestion_and_cleaning.py`](file:///c:/Users/pranshu/Desktop/forest-cover-wildfire/tests/test_ingestion_and_cleaning.py). Zero nulls, valid target classes {1..7}. | `PRESENT_AND_VERIFIED` |

---

### 1.2 Python Core Pipelines & Preprocessing
| Component | Script / Module | Functionality | Evidence | Status |
| :--- | :--- | :--- | :--- | :--- |
| **Source Audit** | [`scripts/01_audit_source.py`](file:///c:/Users/pranshu/Desktop/forest-cover-wildfire/scripts/01_audit_source.py) | SHA-256 fingerprint, schema conformity, domain range checks, outlier baseline. | Generates [`reports/data_quality/validation_report.json`](file:///c:/Users/pranshu/Desktop/forest-cover-wildfire/reports/data_quality/validation_report.json) and markdown audit. | `PRESENT_AND_VERIFIED` |
| **Curated Cleaning** | [`scripts/02_run_cleaning.py`](file:///c:/Users/pranshu/Desktop/forest-cover-wildfire/scripts/02_run_cleaning.py) | Full dataset cleaning, IQR/Z-score outlier tagging, Parquet export. | Tested in `test_schema_conformance`. | `PRESENT_AND_VERIFIED` |
| **Synthetic Cleaning Experiment** | [`scripts/03_synthetic_cleaning_demo.py`](file:///c:/Users/pranshu/Desktop/forest-cover-wildfire/scripts/03_synthetic_cleaning_demo.py) | Controlled 10,000-row sample; exactly 800 continuous cells injected as NaN; median imputation. | Verified: 10,000 rows preserved, exactly 800 missing cells resolved to 0, labels untouched. Generated [`reports/data_quality/synthetic_demo_audit.json`](file:///c:/Users/pranshu/Desktop/forest-cover-wildfire/reports/data_quality/synthetic_demo_audit.json). | `PRESENT_AND_VERIFIED` |
| **EDA & Visualizations** | [`scripts/04_generate_eda.py`](file:///c:/Users/pranshu/Desktop/forest-cover-wildfire/scripts/04_generate_eda.py) | 18 visualization artifacts (scatter, treemaps, radial plots, boxplots, heatmaps). | Artifacts in [`reports/figures/`](file:///c:/Users/pranshu/Desktop/forest-cover-wildfire/reports/figures/). | `PRESENT_AND_VERIFIED` |
| **Descriptive Statistics** | [`scripts/05_descriptive_statistics.py`](file:///c:/Users/pranshu/Desktop/forest-cover-wildfire/scripts/05_descriptive_statistics.py) | 5-number summary, mean, std, skewness, kurtosis, mode, midrange. | [`reports/statistics/descriptive_statistics.csv`](file:///c:/Users/pranshu/Desktop/forest-cover-wildfire/reports/statistics/descriptive_statistics.csv). | `PRESENT_AND_VERIFIED` |
| **Preprocessing Experiments** | [`scripts/06_preprocessing_experiments.py`](file:///c:/Users/pranshu/Desktop/forest-cover-wildfire/scripts/06_preprocessing_experiments.py) | Moving average/Gaussian smoothing, Min-Max, Z-Score, equal-frequency discretization. | [`reports/statistics/preprocessing_comparison.csv`](file:///c:/Users/pranshu/Desktop/forest-cover-wildfire/reports/statistics/preprocessing_comparison.csv). | `PRESENT_AND_VERIFIED` |
| **Feature Selection & PCA** | [`scripts/07_feature_selection_pca.py`](file:///c:/Users/pranshu/Desktop/forest-cover-wildfire/scripts/07_feature_selection_pca.py) | Chi-square & Pearson correlation filtering, PCA 10 components. | Models in `models/pca_*.joblib`, report in `reports/statistics/pca_report.json`. | `PRESENT_AND_VERIFIED` |
| **Classification Models** | [`scripts/08_train_classifiers.py`](file:///c:/Users/pranshu/Desktop/forest-cover-wildfire/scripts/08_train_classifiers.py) | Decision Tree, Random Forest, KNN. | Models serialized: `models/random_forest.joblib` (20.2 MB), `models/decision_tree.joblib` (2.6 MB). | `PRESENT_AND_VERIFIED` |
| **Unsupervised Clustering** | [`scripts/09_run_clustering.py`](file:///c:/Users/pranshu/Desktop/forest-cover-wildfire/scripts/09_run_clustering.py) | K-Means clustering (k=5), silhouette analysis, cluster profiles. | [`reports/statistics/cluster_profiles.csv`](file:///c:/Users/pranshu/Desktop/forest-cover-wildfire/reports/statistics/cluster_profiles.csv). | `PRESENT_AND_VERIFIED` |
| **Forest Fires Regression** | [`scripts/10_train_fires_regression.py`](file:///c:/Users/pranshu/Desktop/forest-cover-wildfire/scripts/10_train_fires_regression.py) | Ridge, Lasso, Random Forest Regressor on log1p(area). | [`reports/statistics/forest_fires_regression_results.csv`](file:///c:/Users/pranshu/Desktop/forest-cover-wildfire/reports/statistics/forest_fires_regression_results.csv). | `PRESENT_AND_VERIFIED` |

---

### 1.3 Supabase & Database Layer
| Item | File Path | Functionality | Evidence | Status |
| :--- | :--- | :--- | :--- | :--- |
| **Supabase SQL Migration** | [`database/supabase_migration.sql`](file:///c:/Users/pranshu/Desktop/forest-cover-wildfire/database/supabase_migration.sql) | DDL for `raw`, `curated`, `analytics`, `models`, `app` schemas with indexes & RLS policies. | 227 lines of SQL. Verified table definitions, RLS statements, indexes. | `PRESENT_AND_VERIFIED` (Static DDL) |
| **Database Engine Connector** | [`python_src/database.py`](file:///c:/Users/pranshu/Desktop/forest-cover-wildfire/python_src/database.py) | SQLAlchemy pool pre-ping connection pooler, batch loader, Supabase REST client factory. | Tested in `test_database_health_check_without_db`. Gracefully enters `STANDALONE_MODE` when offline. | `PRESENT_AND_VERIFIED` |
| **Live Supabase Connection** | Environment / Remote | Direct pooler connection (`SUPABASE_DB_URL`, `SUPABASE_KEY`). | Credentials not set in `.env` (no active `.env` file exists). Live cloud operations cannot execute without user-provided credentials. | `BLOCKED_BY_CREDENTIALS` |

---

### 1.4 FastAPI Backend
| Endpoint / Service | File Path | Functionality | Evidence | Status |
| :--- | :--- | :--- | :--- | :--- |
| **FastAPI Core App** | [`backend/main.py`](file:///c:/Users/pranshu/Desktop/forest-cover-wildfire/backend/main.py) | Primary application server with CORS, error handling, Pydantic validation. | Tested via `fastapi.testclient.TestClient(app)`. | `PRESENT_AND_VERIFIED` |
| **Health & Supabase Status** | `GET /health`, `GET /api/supabase/status` | Returns system health, database mode, model inventory. | Status 200 OK. | `PRESENT_AND_VERIFIED` |
| **Dataset & Statistics** | `GET /api/dataset/*`, `GET /api/statistics/*` | Returns summary, class distribution, data dictionary, descriptive stats. | Status 200 OK across endpoints. | `PRESENT_AND_VERIFIED` |
| **Model Inference** | `POST /api/predict` | Validates 54-feature vector, loads cached joblib model, outputs prediction + class probabilities. | Tested with test payload; returns predicted class 1 (Spruce/Fir). | `PRESENT_AND_VERIFIED` |
| **API Route Versioning** | `GET /api/v1/*` | Explicit `/api/v1/*` paths required by master contract. | Currently routes are registered under `/api/*`; route aliases needed for contract compliance. | `PARTIALLY_IMPLEMENTED` (Remediated in Phase F) |

---

### 1.5 Next.js & TypeScript Frontend
| Component | File Path | Functionality | Evidence | Status |
| :--- | :--- | :--- | :--- | :--- |
| **Next.js Application** | [`frontend/src/app/page.tsx`](file:///c:/Users/pranshu/Desktop/forest-cover-wildfire/frontend/src/app/page.tsx) | 12 full views covering EDA, cleaning, pipeline DAG, prediction playground, governance. | Dev server running on `http://localhost:3000/`. Compiles and renders all 12 views. | `PRESENT_AND_VERIFIED` |
| **Frontend-to-Backend Link** | `page.tsx` line 317 | Configured `NEXT_PUBLIC_API_URL` pointing to `http://localhost:8000`. | Health check, pipeline status, and `POST /api/predict` wired via `fetch()`. Additional tab auto-fetch hooks needed. | `PARTIALLY_IMPLEMENTED` (Remediated in Phase G) |

---

### 1.6 KNIME Analytics Platform Workflows
| Workflow | File Path | Native Application Status | Evidence | Status |
| :--- | :--- | :--- | :--- | :--- |
| **KNIME Installed Application** | `C:\Users\pranshu\AppData\Local\Programs\KNIME\knime.exe` | KNIME 5.12.0 64-bit desktop application installed on host. | Binary confirmed via desktop shortcut resolution. | `PRESENT_AND_VERIFIED` |
| **01 Data Import & Quality** | [`knime/01_data_import_and_quality`](file:///c:/Users/pranshu/Desktop/forest-cover-wildfire/knime/01_data_import_and_quality) | Ingestion, schema audit, and statistics. | Workflow XML exists; node settings subdirectories need generation for standalone loading. | `REQUIRES_MANUAL_GUI` |
| **02 Missing Values Imputation** | [`knime/02_missing_values_imputation`](file:///c:/Users/pranshu/Desktop/forest-cover-wildfire/knime/02_missing_values_imputation) | Synthetic 800-cell imputation. | Workflow XML exists; output CSV in `exports/knime_outputs/`. | `REQUIRES_MANUAL_GUI` |
| **03 Feature Selection & PCA** | [`knime/03_feature_selection_pca`](file:///c:/Users/pranshu/Desktop/forest-cover-wildfire/knime/03_feature_selection_pca) | Normalizer + PCA Compute. | Workflow XML exists; parity check in `test_roundtrip_knime_and_tableau_integration`. | `REQUIRES_MANUAL_GUI` |
| **04 Classification Models** | [`knime/04_classification_comparison`](file:///c:/Users/pranshu/Desktop/forest-cover-wildfire/knime/04_classification_comparison) | Decision Tree, Random Forest, Scorer. | Workflow XML exists. | `REQUIRES_MANUAL_GUI` |
| **05 Clustering K-Means** | [`knime/05_clustering_kmeans`](file:///c:/Users/pranshu/Desktop/forest-cover-wildfire/knime/05_clustering_kmeans) | Normalizer + k-Means (k=5). | Workflow XML exists. | `REQUIRES_MANUAL_GUI` |
| **06 Regression Forest Fires** | [`knime/06_regression_forest_fires`](file:///c:/Users/pranshu/Desktop/forest-cover-wildfire/knime/06_regression_forest_fires) | Math Formula log1p + Linear Regression. | Workflow XML exists. | `REQUIRES_MANUAL_GUI` |
| **07 Preprocessing Experiments** | `knime/07_preprocessing_experiments` | Smoothing, normalization, correlation, Chi-Square, binning. | Workflow directory not yet initialized. | `MISSING` (To be created in Phase H) |

---

### 1.7 Tableau Desktop / Public Workbooks & Data Sources
| Workbook | File Path | Data Source Reference | Audit Finding | Status |
| :--- | :--- | :--- | :--- | :--- |
| **Tableau Installed App** | `C:\Program Files\Tableau\Tableau Public 2026.2\bin\tabpublic.exe` | Tableau Public 2026.2 installed on host. | Verified binary path. | `PRESENT_AND_VERIFIED` |
| **Workbook 01: Executive Overview** | [`tableau/01_executive_forest_cover_overview.twb`](file:///c:/Users/pranshu/Desktop/forest-cover-wildfire/tableau/01_executive_forest_cover_overview.twb) | `tableau_cover_type_summary.csv` | XML valid, but references `tableau_cover_type_summary.csv` which was not created by `11_export_integrations.py`. | `PARTIALLY_IMPLEMENTED` (Remediated in Phase I) |
| **Workbook 02: Terrain Analysis** | [`tableau/02_terrain_and_cover_type_analysis.twb`](file:///c:/Users/pranshu/Desktop/forest-cover-wildfire/tableau/02_terrain_and_cover_type_analysis.twb) | `tableau_terrain_profile.csv` | XML valid, but references `tableau_terrain_profile.csv` which was not generated. | `PARTIALLY_IMPLEMENTED` (Remediated in Phase I) |
| **Workbook 03: Model & Risk** | [`tableau/03_model_performance_and_risk_screening.twb`](file:///c:/Users/pranshu/Desktop/forest-cover-wildfire/tableau/03_model_performance_and_risk_screening.twb) | `tableau_model_comparison.csv` & `wildfire_screening_aggregates.csv` | XML valid, but `tableau_model_comparison.csv` missing and aggregate fields slightly misaligned. | `PARTIALLY_IMPLEMENTED` (Remediated in Phase I) |

---

## 2. Summary of Gaps to Remediate

1. **Tableau Data Source Mismatch:** Generate `tableau_cover_type_summary.csv`, `tableau_terrain_profile.csv`, and `tableau_model_comparison.csv` in `exports/tableau/` matching the exact XML schema expected by the 3 `.twb` workbooks.
2. **KNIME Node Structures & Workflow 7:** Generate node setting folders for all 6 existing KNIME workflows and add `07_preprocessing_experiments`.
3. **FastAPI Route Aliases & Prediction History:** Add `/api/v1/*` aliases in `backend/main.py` and implement prediction persistence logging to Supabase `app.prediction_requests` (or local file fallback).
4. **Next.js Live Fetch Hooks:** Connect tabs to live FastAPI endpoints with proper fallback states.
5. **Integration Contracts & Central Schema Registry:** Create `docs/integration_contracts.md`, `docs/data_dictionary.md`, `config/data_contract.yaml`, and `docs/end_to_end_integration_matrix.csv`.
