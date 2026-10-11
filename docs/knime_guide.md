# KNIME Workflows Comprehensive User Guide
## Forest Cover Type Prediction & Wildfire-Risk Analysis

---

## 1. Prerequisites & KNIME Environment
- **KNIME Analytics Platform**: Version 5.1+ recommended
- **Required Extensions**:
  - KNIME Base Nodes (built-in)
  - KNIME JavaScript Views / Views (Labs)
  - KNIME Ensemble Learning (Random Forest)
- **Data Location**: Set relative or absolute path to `exports/knime/` in the project workspace.

---

## 2. Detailed Workflow Configurations

### Workflow 1: Data Quality & Profiling (`01_data_quality_profiling`)
- **Input**: `exports/knime/covertype_curated.csv`
- **Node 1: CSV Reader**:
  - Delimiter: `,`, Quotes: `"`, Has Column Header: `true`
  - Limit rows: optional for preview, or complete table (50,000 curated rows).
- **Node 2: Missing Value**:
  - Configure to detect NaN/empty cells across all columns.
  - Expected verification: 0 missing cells found.
- **Node 3: Statistics**:
  - Select all 10 continuous predictors (`Elevation`, `Aspect`, `Slope`, etc.).
  - Output port 1: Descriptive statistics summary (Mean, Std, Min, Max, Median, Skewness).
- **Node 4: Data Explorer**:
  - Interactive histogram view of distribution shapes and class frequencies.

### Workflow 2: Feature Selection & PCA (`02_feature_selection_pca`)
- **Input**: `exports/knime/covertype_curated.csv`
- **Node 1: Column Filter**:
  - Exclude `Cover_Type` (isolate predictors from target).
- **Node 2: Normalizer**:
  - Mode: Z-Score Normalization (Gaussian scaling $\mu=0, \sigma=1$).
- **Node 3: PCA Apply / PCA (Compute)**:
  - Variance retention: 95% or fixed 5 components.
  - Output: Eigenvalue table, component loadings, projected data.
- **Node 4: Linear Correlation**:
  - Computes Pearson correlation matrix; outputs correlation filter view.
- **Verification**: Verify that `Elevation` is the primary contributor to PC1 loadings.

### Workflow 3: Classification Model Comparison (`03_classification_comparison`)
- **Input**: `exports/knime/covertype_curated.csv`
- **Node 1: Partitioning**:
  - 80% First partition (Training), 20% Second partition (Testing).
  - Mode: **Stratified sampling** on `Cover_Type` with Random Seed `42`.
- **Branch A (Decision Tree)**:
  - **Decision Tree Learner**: Quality measure: Gini index, Max depth: 20, Min records per node: 5.
  - **Decision Tree Predictor**: Evaluates on the 20% test partition.
- **Branch B (Random Forest)**:
  - **Random Forest Learner**: Number of trees: 100, Attribute sampling: Square root of $M$.
  - **Random Forest Predictor**: Evaluates on test partition.
- **Node 4: Scorer**:
  - Compares True `Cover_Type` vs `Prediction (Cover_Type)`.
  - Generates Accuracy, Cohen's Kappa, and Confusion Matrix.
  - Verification: RF test accuracy reaches ~85%–90%, consistent with Python results in `classification_metrics.csv`.

### Workflow 4: Topographic Clustering (`04_clustering`)
- **Input**: `exports/knime/covertype_curated.csv`
- **Node 1: Column Filter**: Keep 10 continuous predictors only.
- **Node 2: Normalizer**: Z-score standardization.
- **Node 3: k-Means**:
  - Number of clusters: $k = 7$, Max iterations: 100.
- **Node 4: Color Manager**: Assign distinct colors to clusters 0–6.
- **Node 5: 2D Density Plot / Scatter Matrix**: Visualizes cluster boundaries across `Elevation` and `Slope`.
- **Node 6: GroupBy**: Aggregates mean feature values by cluster ID.

### Workflow 5: Forest Fires Burned Area Regression (`05_forest_fires_regression`)
- **Input**: `data/external/forestfires.csv` or `exports/knime/forest_fires_regression_results.csv`
- **Node 1: Math Formula**: `ln(area + 1)` (log1p transformation).
- **Node 2: Partitioning**: 80/20 train/test.
- **Node 3: Linear Regression Learner**:
  - Target: `log_area`. Features: meteorological measurements.
- **Node 4: Numeric Scorer**: Computes $R^2$, MAE, RMSE.

### Workflow 6: Preprocessing Experiments (`06_preprocessing_experiments`)
- **Input**: `exports/knime/covertype_curated.csv`
- **Node 1: Normalizer (Min-Max)**: Maps features to $[0, 1]$.
- **Node 2: Normalizer (Z-Score)**: Centers to mean 0, variance 1.
- **Node 3: Auto-Binner**: Equal-frequency quantile binning into 5 intervals.
- **Node 4: Table View**: Side-by-side verification of original vs transformed values.

---

## 3. Reconciling KNIME with Python
- All random seeds are set to `42` to guarantee alignment.
- When comparing confusion matrices, note that KNIME zero-indexes or one-indexes classes depending on node settings; map using the labels in `data_dictionary.csv`.
