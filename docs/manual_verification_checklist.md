# Manual Verification Checklist & Practical Execution Guide

**Target Applications:** KNIME Analytics Platform (v5.12.0) | Tableau Public (2026.2) | Supabase Cloud Console  
**Host Paths:**
- KNIME Binary: `C:\Users\pranshu\AppData\Local\Programs\KNIME\knime.exe`
- Tableau Public: `C:\Program Files\Tableau\Tableau Public 2026.2\bin\tabpublic.exe`
- Project Workspace: `C:\Users\pranshu\Desktop\forest-cover-wildfire`

---

## 1. KNIME Workflows Interactive Execution Guide

All 7 visual node workflows have been generated in the [`knime/`](file:///c:/Users/pranshu/Desktop/forest-cover-wildfire/knime/) folder with valid node definitions, XML settings, and relative file paths pointing to [`exports/knime/`](file:///c:/Users/pranshu/Desktop/forest-cover-wildfire/exports/knime/) and [`data/`](file:///c:/Users/pranshu/Desktop/forest-cover-wildfire/data/).

### Step 1.1: Launch KNIME Analytics Platform
1. Launch KNIME via the Desktop shortcut or execute:
   ```cmd
   "C:\Users\pranshu\AppData\Local\Programs\KNIME\knime.exe"
   ```
2. Select your default workspace directory when prompted (e.g. `C:\Users\pranshu\knime-workspace`).
3. In KNIME, go to **File → Import KNIME Workflow...**
4. Select **Select root directory** and browse to:
   ```
   C:\Users\pranshu\Desktop\forest-cover-wildfire\knime
   ```
5. Check all 7 workflows to import them into your KNIME workspace:
   - `01_data_import_and_quality`
   - `02_missing_values_imputation`
   - `03_feature_selection_pca`
   - `04_classification_comparison`
   - `05_clustering_kmeans`
   - `06_regression_forest_fires`
   - `07_preprocessing_experiments`

---

### Step 1.2: Workflow Execution Checklist

| Workflow | Key Nodes to Inspect | Manual Execution Steps | Expected Outcome & Evidence |
| :--- | :--- | :--- | :--- |
| **01 Data Import & Quality** (Practical 1) | `CSV Reader (#1)`, `Table Validator (#2)`, `Statistics (#3)` | Double-click `CSV Reader` to verify preview of `exports/knime/covertype_curated.csv`. Click **Execute All Nodes** (Shift+F7). | All nodes show green status dot. Right-click `Statistics` → **View: Extended Statistics** to view 5-number summary and zero null count. |
| **02 Missing Values Imputation** (Practical 2) | `CSV Reader (#1)`, `Missing Value (#2)`, `CSV Writer (#3)` | Open workflow. `CSV Reader` reads `data/processed/covtype_missing_values_demo.csv`. `Missing Value` executes column median imputation. Click **Execute**. | Injected 800 missing cells are filled. Output table shows 10,000 rows with 0 missing cells. Writes to `exports/knime_outputs/knime_synthetic_imputation_audit.csv`. |
| **03 Feature Selection & PCA** (Practical 6) | `CSV Reader (#1)`, `Normalizer (#2)`, `PCA Compute (#3)`, `CSV Writer (#4)` | Open workflow. Inspect `Normalizer` (Z-score). Inspect `PCA Compute` (10 dimensions). Click **Execute**. | Green status. Right-click `PCA Compute` → **Eigenvalues & Cumulative Variance**. Cumulative variance of first 8 components matches ~96.9%. Writes to `exports/knime_outputs/knime_pca_variance.csv`. |
| **04 Classification Models** (Practical 7) | `Partitioning (#2)`, `Decision Tree Learner (#3)`, `Random Forest Learner (#4)`, `Scorer (#5)` | Open workflow. Partitioning (80/20 stratified). Click **Execute**. | Right-click `Scorer` → **View: Confusion Matrix & Accuracy**. Random Forest test accuracy ~93.5% (±1.5%), Decision Tree ~86.6%. Writes to `exports/knime_outputs/knime_classification_metrics.csv`. |
| **05 Clustering K-Means** (Practical 8) | `Column Filter (#2)`, `Normalizer (#3)`, `k-Means (#4)` | Open workflow. Filters continuous predictors, normalizes $[0, 1]$, fits $k=5$. Click **Execute**. | Right-click `k-Means` → **View: Cluster Centroids**. 5 distinct ecological cluster centroids displayed. Writes to `exports/knime_outputs/knime_cluster_centroids.csv`. |
| **06 Regression Forest Fires** (Practical 9) | `CSV Reader (#1)`, `Math Formula (#2)`, `Linear Regression (#4)`, `Numeric Scorer (#5)` | Reads `data/external/forestfires.csv`. Math formula calculates $\ln(\text{area} + 1)$. Click **Execute**. | Right-click `Numeric Scorer` → **View: Numeric Scorer Metrics**. RMSE ~1.41 (±0.05). Writes to `exports/knime_outputs/knime_regression_metrics.csv`. |
| **07 Preprocessing Experiments** (Practical 10) | `Normalizer (#2)`, `Auto-Binner (#3)`, `Correlation Filter (#4)` | Evaluates Min-Max vs Z-Score, equal-frequency quantile binning, and collinearity threshold (0.75). Click **Execute**. | All nodes execute green. Output table shows binned elevation and filtered continuous columns. |

---

## 2. Tableau Dashboards Interactive Verification Guide

Tableau Public 2026.2 is installed at:
`C:\Program Files\Tableau\Tableau Public 2026.2\bin\tabpublic.exe`

All 3 workbooks in [`tableau/`](file:///c:/Users/pranshu/Desktop/forest-cover-wildfire/tableau/) are preconfigured with federated data connections pointing directly to [`exports/tableau/`](file:///c:/Users/pranshu/Desktop/forest-cover-wildfire/exports/tableau/).

### Step 2.1: Open Workbook 1 — Executive Forest Cover Overview
Command to launch:
```cmd
"C:\Program Files\Tableau\Tableau Public 2026.2\bin\tabpublic.exe" "C:\Users\pranshu\Desktop\forest-cover-wildfire\tableau\01_executive_forest_cover_overview.twb"
```
**Verification Checklist:**
1. Data source `Cover Type Summary` connects to `tableau_cover_type_summary.csv`.
2. **Worksheet 1 (Species Prevalence):** Visualizes Lodgepole Pine (48.8%) and Spruce/Fir (36.5%) as dominant classes in a colored treemap.
3. **Worksheet 2 (Elevation by Cover Type):** Bar chart showing Krummholz highest (>3,300m) and Cottonwood lowest (<2,300m).
4. **Dashboard 1:** Both worksheets combine smoothly into an executive 1200×800 overview layout.

---

### Step 2.2: Open Workbook 2 — Terrain and Cover-Type Analysis
Command to launch:
```cmd
"C:\Program Files\Tableau\Tableau Public 2026.2\bin\tabpublic.exe" "C:\Users\pranshu\Desktop\forest-cover-wildfire\tableau\02_terrain_and_cover_type_analysis.twb"
```
**Verification Checklist:**
1. Data source `Terrain Profile` connects to `tableau_terrain_profile.csv` (20,000 stratified observations).
2. **Worksheet 1 (Terrain Scatter: Elevation vs Slope):** Multi-dimensional scatter plot colored by cover species.
3. **Worksheet 2 (Wilderness Area Distribution):** Distribution of species across Rawah, Neota, Comanche Peak, Cache la Poudre.
4. **Dashboard 2:** Interactive cross-filtering by Wilderness Area and Slope.

---

### Step 2.3: Open Workbook 3 — Model Performance and Risk Screening
Command to launch:
```cmd
"C:\Program Files\Tableau\Tableau Public 2026.2\bin\tabpublic.exe" "C:\Users\pranshu\Desktop\forest-cover-wildfire\tableau\03_model_performance_and_risk_screening.twb"
```
**Verification Checklist:**
1. Data source 1 `Model Comparison` connects to `tableau_model_comparison.csv` (Random Forest, Decision Tree, KNN).
2. Data source 2 `Wildfire Risk Aggregates` connects to `wildfire_screening_aggregates.csv`.
3. **Worksheet 1 (Classifier Accuracy Benchmark):** Bar chart comparing model accuracies (Random Forest 93.5% vs Decision Tree 86.6%).
4. **Worksheet 2 (Wildfire Hazard Strata):** Bar chart comparing topographic screening scores by Wilderness Area.
5. **Dashboard 3:** Layout displays side-by-side benchmark comparison and screening risk strata.

---

## 3. Supabase Cloud Database Verification (When Credentials Provided)

When you obtain your Supabase cloud project credentials:
1. Create a `.env` file in the project root based on [`.env.example`](file:///c:/Users/pranshu/Desktop/forest-cover-wildfire/.env.example):
   ```env
   SUPABASE_URL=https://your-project-id.supabase.co
   SUPABASE_KEY=your-service-role-or-anon-key
   SUPABASE_DB_URL=postgresql+psycopg://postgres.your-project-id:your-db-password@aws-0-us-east-1.pooler.supabase.com:6543/postgres
   ```
2. Run database migration to apply schema DDL:
   ```bash
   .venv\Scripts\python.exe scripts\12_load_supabase.py
   ```
3. Verify table counts and RLS in your Supabase web dashboard:
   - `raw.source_manifests`: 1 row (hash `ea35ca68...`)
   - `curated.forest_cover`: 50,000 curated rows with outlier flags
   - `analytics.descriptive_statistics`: 10 rows
   - `models.evaluation_metrics`: 3 model rows
   - `app.prediction_requests`: Tracks live predictions submitted from the frontend
