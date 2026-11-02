# KNIME Workflows Comprehensive User Guide (Plan v2)
## Forest Cover Type Prediction & Wildfire-Risk Analysis
### Aligned with Plan v2 Section 5 & Practicals 6a–9

---

## 1. Overview & Workspace Structure

The KNIME workflows reside in `knime/` and correspond directly to the 5 official workflows catalogued in Section 5 of **Implementation Plan v2**:

```
knime/
├── 01_quality_and_profile/          # Practical 6a (Data quality checks, statistics, range validation)
├── 02_feature_selection_pca/        # Practical 6b (Standardized PCA scree, feature ranking, scatter plot)
├── 03_classification/               # Practical 7 (Decision Tree, Random Forest, KNN on 80/20 split)
├── 04_clustering/                   # Practical 8 (K-Means k=2..12, silhouette, cluster profiling)
├── 05_fires_regression/             # Practical 9 (Burned area log1p regression, tree vs linear)
├── Example Workflows/               # Reference workflows from KNIME distribution
└── README.md                        # Quick reference and node configurations
```

---

## 2. Opening & Running Workflows in KNIME

### Step 1: Open KNIME Workspace
1. Launch **KNIME Analytics Platform 5.2 / 5.3**.
2. When prompted for workspace location, browse to your project root folder:
   `c:\Users\pranshu\Desktop\forest-cover-wildfire\knime`
3. In the **KNIME Explorer** panel, you will see the 5 workflows:
   - `01_quality_and_profile`
   - `02_feature_selection_pca`
   - `03_classification`
   - `04_clustering`
   - `05_fires_regression`

### Step 2: Execution Modes
Each workflow is pre-configured with **relative path filehandling** (`knime.workflow` relative paths pointing to `../../exports/knime/` and `../../exports/knime_outputs/`).
If connecting to PostgreSQL/Supabase:
1. Double-click the **PostgreSQL Connector** or **DB Connector** node.
2. Enter host, database name (`forest_hub`), and credentials for role `bi_reader`.
3. Switch the Reader node from `CSV Reader` to `DB Query Reader`.

---

## 3. Workflow-by-Workflow Guide

### Workflow 01: `01_quality_and_profile` (Practical 6a)
- **Objective**: Audit dataset schema integrity, verify zero missing values, check range constraints, and compute group statistics.
- **Node Pipeline**:
  `CSV Reader` / `DB Query Reader` $\to$ `Statistics` $\to$ `Missing Value` $\to$ `Duplicate Row Filter` $\to$ `Rule Engine` $\to$ `GroupBy` $\to$ `Constant Value Column (run_id)` $\to$ `CSV Writer` / `DB Writer`.
- **Key Rules in Rule Engine**:
  ```text
  $Aspect$ >= 0 AND $Aspect$ <= 360 => "VALID_ASPECT"
  $Slope$ >= 0 AND $Slope$ <= 90 => "VALID_SLOPE"
  $Hillshade_Noon$ >= 0 AND $Hillshade_Noon$ <= 255 => "VALID_HILLSHADE"
  $Horizontal_Distance_To_Hydrology$ >= 0 => "VALID_DIST_HYDRO"
  TRUE => "CHECK_PASSED"
  ```
- **Output**: `exports/knime_outputs/knime_quality_checks.csv` (table: `analytics.knime_quality_checks`).

### Workflow 02: `02_feature_selection_pca` (Practical 6b)
- **Objective**: Compare standardized 10-feature continuous PCA against all 54 features, compute cumulative variance, and examine feature correlation.
- **Node Pipeline**:
  - **Branch 1 (Continuous PCA)**: `Row Splitter` (split='train') $\to$ `Column Filter` (10 continuous) $\to$ `Normalizer` (Z-score) $\to$ `PCA Compute` $\to$ `PCA Apply` (test set) $\to$ `Math Formula` (cumulative variance) $\to$ `CSV Writer`.
  - **Branch 2 (Feature Ranking & Viz)**: `Low Variance Filter` $\to$ `Linear Correlation` $\to$ `Color Manager` $\to$ `Scatter Plot` (PC1 vs PC2 colored by `Cover_Type`).
- **Outputs**:
  - `knime_pca_variance.csv` (PC1 to PC8 cumulative explained variance, reaching $>96.9\%$).
  - `knime_feature_ranks.csv` (rankings identifying `Elevation` and distance variables as top predictors).

### Workflow 03: `03_classification` (Practical 7)
- **Objective**: Evaluate Decision Tree, Random Forest, and K-Nearest Neighbors on the identical 80/20 stratified split (`seed=42`).
- **Node Pipeline**:
  `Partitioning` (80/20 Stratified on `Cover_Type`) $\to$ `Decision Tree Learner/Predictor` + `Random Forest Learner/Predictor` + `Row Sampling` $\to$ `K Nearest Neighbor` $\to$ `Scorer` $\to$ `Constant Value (run_id)` $\to$ `CSV Writer`.
- **Expected Benchmark**:
  - Random Forest: Accuracy $\approx 92.8\%$, Macro F1 $\approx 0.899$.
  - Decision Tree: Accuracy $\approx 86.1\%$, Macro F1 $\approx 0.798$.
  - KNN (20k sample): Accuracy $\approx 81.4\%$, Macro F1 $\approx 0.741$.
- **Output**: `exports/knime_outputs/knime_classification_metrics.csv`.

### Workflow 04: `04_clustering` (Practical 8)
- **Objective**: Unsupervised topographic clustering using K-Means and profile each terrain cluster.
- **Node Pipeline**:
  `Column Filter` (10 continuous) $\to$ `Normalizer` (Z-score) $\to$ `Counting Loop Start (k=2..12)` $\to$ `k-Means` $\to$ `Silhouette Coefficient` $\to$ `Loop End` $\to$ `k-Means final (k=7)` $\to$ `Cluster Assigner` $\to$ `Joiner (Cover_Type re-attached AFTER fit)` $\to$ `GroupBy (medians, dominant class)` $\to$ `CSV Writer`.
- **Scientific Guardrail**: `Cover_Type` is strictly excluded from clustering inputs and joined only afterwards for cluster characterization.
- **Output**: `exports/knime_outputs/knime_cluster_centroids.csv` and `knime_cluster_profiles.csv`.

### Workflow 05: `05_fires_regression` (Practical 9)
- **Objective**: Model burned area from weather conditions using raw vs $\log(1 + \text{area})$ targets.
- **Node Pipeline**:
  `CSV Reader` (`forestfires.csv`) $\to$ `Math Formula (log(area+1))` $\to$ `Partitioning (80/20)` $\to$ `Linear Regression Learner` & `Random Forest Regression Learner` $\to$ `Regression Predictor` $\to$ `Math Formula (exp(y) - 1 inverse)` $\to$ `Numeric Scorer` $\to$ `CSV Writer`.
- **Output**: `exports/knime_outputs/knime_regression_metrics.csv`.

---

## 4. Parity & Reconciliations Checklist

- [x] All 5 Plan v2 workflows present in `knime/`.
- [x] Relative path filehandling configured for portability (`knime.workflow`).
- [x] `run_id` audit column present on all exported tables.
- [x] Random seeds locked to `42` to match Python splits.
- [x] Python parity tests verified within stated tolerance ($\le \pm 2.0\%$ for tree models).
