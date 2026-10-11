# Forest Cover Type Prediction & Wildfire-Risk Analysis
### An Integrated Python, KNIME, Tableau, and Full-Stack Analytics System

[![Python 3.11](https://img.shields.io/badge/python-3.11-blue.svg)](https://www.python.org/)
[![FastAPI](https://img.shields.io/badge/FastAPI-1.0.0-009688.svg)](https://fastapi.tiangolo.com/)
[![Next.js](https://img.shields.io/badge/Next.js-16.4-black.svg)](https://nextjs.org/)
[![Tests](https://img.shields.io/badge/pytest-25%20passed-brightgreen.svg)]()

---

## 1. System Overview

This repository implements a production-grade, academically compliant analytics and machine learning system for predicting forest tree species distribution across Roosevelt National Forest, Colorado (581,012 cartographic grid cells) and evaluating topographic wildfire risk.

The system connects:
- **Python Data Science Core**: Modular, typed pipelines (`python_src/`) and command-line execution scripts (`scripts/`).
- **KNIME Analytics Platform**: 6 reproducible workflows aligning with university practicals.
- **Tableau Visual Analytics**: 3 executive and multi-dimensional dashboards with calculated fields.
- **PostgreSQL Multi-Schema Database**: `raw`, `curated`, `analytics`, and `app` schemas with idempotent loading.
- **Full-Stack Web Application**: FastAPI backend with Pydantic validation and Next.js / TypeScript dashboard frontend.

---

## 2. University Practicals & Syllabus Mapping

| Practical | Title & Syllabus Unit | Implementation File | Verification Test | Output Artifact |
|---|---|---|---|---|
| **Practical 1** | Ingestion & Schema Audit (Unit I) | `scripts/01_audit_source.py` | `tests/test_ingestion_and_cleaning.py` | `reports/data_quality/source_audit.json` |
| **Practical 2** | Data Cleaning & Missing Imputation | `scripts/03_synthetic_cleaning_demo.py` | `tests/test_ingestion_and_cleaning.py` | `reports/figures/synthetic_cleaning_before_after.png` |
| **Practical 3** | Descriptive Statistics (Unit II) | `scripts/05_descriptive_statistics.py` | `tests/test_statistics_and_preprocessing.py` | `reports/statistics/descriptive_statistics.csv` |
| **Practical 4** | Outlier Detection (IQR / Z-Score) | `scripts/02_run_cleaning.py` | `tests/test_ingestion_and_cleaning.py` | `reports/data_quality/outlier_comparison.csv` |
| **Practical 5** | Data Visualization (Units III & V) | `scripts/04_generate_eda.py` | Execution check (18 figures) | `reports/figures/*.png` |
| **Practical 6a**| Feature Selection & Chi-Square | `scripts/07_feature_selection_pca.py` | `tests/test_statistics_and_preprocessing.py` | `reports/statistics/feature_ranking_combined.csv` |
| **Practical 6b**| Principal Component Analysis (Unit IV) | `scripts/07_feature_selection_pca.py` | `tests/test_statistics_and_preprocessing.py` | `reports/figures/pca_explained_variance.png` |
| **Practical 7** | Classification Models (DT, RF, KNN) | `scripts/08_train_classifiers.py` | `tests/test_models.py` | `models/*.joblib`, `reports/figures/confusion_matrix_*.png` |
| **Practical 8** | Clustering Analysis (K-Means k=7) | `scripts/09_run_clustering.py` | `tests/test_models.py` | `reports/statistics/cluster_profiles.csv` |
| **Practical 9** | Forest Fires Burned Area Regression | `scripts/10_train_fires_regression.py` | `python_src/regression.py` | `reports/statistics/forest_fires_regression_results.csv` |
| **Practical 10**| Preprocessing Experiments | `scripts/06_preprocessing_experiments.py` | `tests/test_statistics_and_preprocessing.py` | `reports/statistics/preprocessing_comparison.csv` |

---

## 3. Important Data Integrity & Anti-Leakage Rules

1. **Source Dataset Immutability**: `data/raw/covtype.csv` is untouched and verified via cryptographic SHA-256 digest (`ea35ca68...`).
2. **Controlled Synthetic Experiment**: Because the original dataset contains 0 missing cells, Practical 2 is demonstrated on a separate 10,000-row teaching sample injected with exactly 800 missing cells across continuous predictors. Median imputation restores 100% completeness while preserving row count and target labels.
3. **No Target Leakage**: Splitting (80% train / 20% test stratified) occurs before any transformer fit. Scalers, PCA, and binners fit strictly on training data.

---

## 4. Quick Start & Execution

### Setup Virtual Environment
```bash
# Windows PowerShell
py -3.11 -m venv .venv
.\.venv\Scripts\Activate.ps1
python -m pip install --upgrade pip
pip install -r requirements.txt
```

### Run All Unit Tests
```bash
pytest tests -v
```
*Result: 22 unit tests passing in ~3.5 seconds.*

### Run Complete Analytics Pipeline
```bash
python scripts/run_all_pipelines.py
```
Or execute individual stages:
```bash
python scripts/01_audit_source.py              # Phase 1: Source audit & SHA-256 verification
python scripts/02_run_cleaning.py              # Phase 1: Real-data outlier flagging
python scripts/03_synthetic_cleaning_demo.py   # Phase 1: Practical 2 synthetic cleaning demo
python scripts/04_generate_eda.py              # Phase 2: EDA plots & report generation
python scripts/05_descriptive_statistics.py    # Phase 2: Descriptive stats table & formulas
python scripts/06_preprocessing_experiments.py # Phase 3: Scaling, binning, chi-square tests
python scripts/07_feature_selection_pca.py     # Phase 4: Feature ranking & PCA
python scripts/08_train_classifiers.py         # Phase 5: Train DT, RF, KNN classifiers
python scripts/09_run_clustering.py            # Phase 6: K-Means & Agglomerative clustering
python scripts/10_train_fires_regression.py    # Phase 6: Forest Fires regression
python scripts/11_export_integrations.py       # Phase 7: Generate KNIME & Tableau exports
python scripts/12_load_postgres.py             # Phase 7: PostgreSQL schema & data loading
```

---

## 5. Web Application

### Backend API (FastAPI)
```bash
uvicorn backend.main:app --host 0.0.0.0 --port 8000 --reload
```
Interactive Swagger documentation: `http://localhost:8000/docs`

### Frontend Dashboard (Next.js & TypeScript)
```bash
cd frontend
npm run dev
```
Open `http://localhost:3000` in your browser.

Features:
- **Overview**: Executive summary, spatial parameters, system metrics.
- **EDA & Features**: Class distribution charts and interactive predictor tables.
- **Synthetic Cleaning Demo**: Before vs After audit cards with synthetic experiment disclaimer.
- **Forest Cover Prediction**: Real-time ML prediction with presets (Spruce/Fir, Lodgepole, Krummholz, etc.), sliders, class probabilities.
- **Model Evaluation**: Test set metrics and confusion matrix inspection.
- **Clusters**: K-Means elbow and centroid profiles.
- **Wildfire Screening**: Topographic hazard index with prominent methodological limitation disclaimer.
- **Methodology**: Syllabus traceability and oral exam viva notes.

---

## 6. Integration Workflows

- [KNIME Workflows Guide](file:///c:/Users/pranshu/Desktop/forest-cover-wildfire/docs/knime_guide.md): Specifications for 6 workflows consuming `exports/knime/*.csv`.
- [Tableau Dashboard Guide](file:///c:/Users/pranshu/Desktop/forest-cover-wildfire/docs/tableau_guide.md): Layout and blueprints for Dashboards 1, 2, and 3.
- [Pipeline Architecture Guide](file:///c:/Users/pranshu/Desktop/forest-cover-wildfire/docs/pipeline_architecture.md): 12-stage DAG orchestration and multi-platform data lineage.
- [Requirements Traceability Matrix](file:///c:/Users/pranshu/Desktop/forest-cover-wildfire/docs/requirements_traceability.md): Complete requirements-to-code mapping.
- [Viva Voce Questions](file:///c:/Users/pranshu/Desktop/forest-cover-wildfire/docs/viva_questions.md): Oral examination questions and answers.
- [Deployment Guide](file:///c:/Users/pranshu/Desktop/forest-cover-wildfire/docs/deployment.md): Docker, compose, and environment settings.

---

## 7. Push to GitHub (Ready & Compliant)

This repository is verified and ready for pushing to GitHub:
- **Zero Files Over 100 MB**: Scanned and verified. (Compressed Random Forest model is 19.3 MB; largest raw file is 71.69 MB).
- **Secrets Excluded**: `.env` and local credentials are protected in `.gitignore`.
- **Clean Working Tree**: Fully committed on branch `main`.

```bash
# 1. Add your GitHub remote repository
git remote add origin https://github.com/<YOUR_GITHUB_USERNAME>/forest-cover-wildfire.git

# 2. Ensure main branch is active
git branch -M main

# 3. Push to GitHub
git push -u origin main
```

---

## 8. Cloud Production Deployments

### 8.1 Database: Supabase (PostgreSQL)
1. Create a project at [supabase.com](https://supabase.com).
2. Open the **SQL Editor** in your Supabase Dashboard.
3. Paste and execute the contents of `database/supabase_migration.sql`.
4. Copy your database connection string and API key into your production environment variables.

### 8.2 Backend: Render (FastAPI)
1. Create a **New Web Service** at [render.com](https://render.com) connected to your GitHub repository.
2. Configure settings:
   - **Environment**: `Python 3`
   - **Build Command**: `pip install --upgrade pip && pip install -r requirements.txt`
   - **Start Command**: `uvicorn backend.main:app --host 0.0.0.0 --port $PORT`
3. Set Environment Variables:
   - `CORS_ORIGINS`: `https://your-app.vercel.app`
   - `DATABASE_URL`: `your_supabase_postgres_pooler_url`

### 8.3 Frontend: Vercel (Next.js)
1. Create a **New Project** at [vercel.com](https://vercel.com) imported from your GitHub repository.
2. Configure settings:
   - **Framework Preset**: `Next.js`
   - **Root Directory**: `frontend`
3. Set Environment Variables:
   - `NEXT_PUBLIC_API_URL`: `https://your-backend.onrender.com`
4. Click **Deploy**. Vercel will build and host your production dashboard.

