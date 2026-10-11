# Practical Mapping & Lab Manual
## Forest Cover Type Prediction & Wildfire-Risk Analysis

This guide maps each academic practical (1–10) directly to executable scripts, theoretical background, mathematical formulas, and university submission evidence.

---

## Practical 1: Ingestion & Handling of Tabular Data
- **Syllabus Unit**: Unit I (Data Ingestion & Architectures)
- **Script**: `scripts/01_audit_source.py`
- **Theory**: High-volume tabular spatial observations require verification of row/column dimensions, encoding, delimiters, and cryptographic checksums to prevent silent data corruption.
- **Formulas / Concepts**:
  - SHA-256 Digest: $H(m) = \text{SHA256}(m)$
- **Output Artifacts**:
  - `reports/data_quality/source_audit.json`
  - `data/data_manifest.json`
- **Submission Evidence**: Record verification of 581,012 rows, 55 columns, and zero missing values in untouched raw source.

---

## Practical 2: Data Cleaning & Missing Value Imputation
- **Syllabus Unit**: Unit I (Data Preprocessing & Cleaning)
- **Script**: `scripts/02_run_cleaning.py`, `scripts/03_synthetic_cleaning_demo.py`
- **Theory**: When real datasets are complete, cleaning protocols must be proven via controlled synthetic experiments. Missing values in continuous terrain features are imputed via column median to resist extreme skewness. Target and binary columns are strictly excluded.
- **Formulas / Concepts**:
  - Median Imputation: $\tilde{x} = \text{median}(X_{\text{observed}})$
- **Output Artifacts**:
  - `data/processed/covtype_missing_values_demo_clean.csv`
  - `reports/data_quality/synthetic_demo_audit.json`
  - `reports/figures/synthetic_cleaning_before_after.png`
- **Submission Evidence**: Verification of exact 800 injected missing cells, restored to 0 missing cells, preserving 10,000 rows.

---

## Practical 3: Descriptive Statistics & Distribution Analysis
- **Syllabus Unit**: Unit II (Descriptive Statistics & Sampling)
- **Script**: `scripts/05_descriptive_statistics.py`
- **Theory**: Quantitative characterization of central tendency, dispersion, and shape for spatial predictors.
- **Formulas / Concepts**:
  - Mean: $\mu = \frac{1}{N}\sum_{i=1}^N x_i$
  - Variance: $\sigma^2 = \frac{1}{N-1}\sum_{i=1}^N (x_i - \bar{x})^2$
  - Five-Number Summary: $[\text{Min}, Q_1, \text{Median}, Q_3, \text{Max}]$
  - Skewness: $\gamma_1 = \frac{\frac{1}{N}\sum (x_i - \bar{x})^3}{\sigma^3}$
- **Output Artifacts**:
  - `reports/statistics/descriptive_statistics.csv`
  - `reports/practical_evidence/practical3_statistics.md`

---

## Practical 4: Outlier Detection (IQR & Z-Score)
- **Syllabus Unit**: Unit II (Exploratory Data Analysis)
- **Script**: `scripts/02_run_cleaning.py`
- **Theory**: Topographic variables often feature extreme natural terrain (e.g. 5,000m roadway distances or 50° slopes). Outliers are flagged for analytical awareness rather than discarded to preserve valid geographic extremes.
- **Formulas / Concepts**:
  - IQR Fencing: $[Q_1 - 1.5 \cdot \text{IQR}, Q_3 + 1.5 \cdot \text{IQR}]$ where $\text{IQR} = Q_3 - Q_1$
  - Standardized Z-Score: $z_i = \frac{x_i - \mu}{\sigma}$, outlier if $|z_i| > 3.0$
- **Output Artifacts**:
  - `reports/data_quality/outlier_comparison.csv`
  - `reports/figures/continuous_boxplots.png`

---

## Practical 5: Comprehensive Data Visualization
- **Syllabus Unit**: Units III & V (Visual Design & Perception)
- **Script**: `scripts/04_generate_eda.py`
- **Theory**: Multidimensional visual encoding using preattentive visual attributes (color hue, spatial position, length).
- **Chart Types Implemented**:
  1. XY Scatter & Density Plots (Elevation vs Distance to Hydrology)
  2. Grouped & Stacked Bar Charts (Cover Type by Wilderness Area)
  3. Radial Polar Plots (Circular cover type distributions)
  4. Squarified Treemaps (Proportional forest cover areas)
  5. Correlation Heatmap Matrices (Full continuous predictor collinearity)
  6. Boxplots & Small Multiples (Per-class terrain distributions)
- **Output Artifacts**: 18 PNG figures in `reports/figures/`

---

## Practical 6a: Feature Selection & Hypothesis Testing
- **Syllabus Unit**: Unit IV (Feature Engineering)
- **Script**: `scripts/07_feature_selection_pca.py`
- **Theory**: Identify non-redundant, highly predictive features using statistical dependence tests.
- **Formulas / Concepts**:
  - Chi-Square Test of Independence: $\chi^2 = \sum \frac{(O_i - E_i)^2}{E_i}$ (computed on scaled non-negative predictors)
  - Pearson Correlation: $r = \frac{\sum (x_i - \bar{x})(y_i - \bar{y})}{\sqrt{\sum (x_i - \bar{x})^2 \sum (y_i - \bar{y})^2}}$
- **Output Artifacts**:
  - `reports/statistics/feature_ranking_combined.csv`

---

## Practical 6b: Principal Component Analysis (PCA)
- **Syllabus Unit**: Unit IV (Dimensionality Reduction)
- **Script**: `scripts/07_feature_selection_pca.py`
- **Theory**: Orthogonal linear transformation that projects continuous predictors onto eigenvectors of maximum variance, alleviating the curse of dimensionality.
- **Formulas / Concepts**:
  - Covariance matrix $\Sigma = \frac{1}{n} X^T X$
  - Eigendecomposition $\Sigma v_k = \lambda_k v_k$
  - Explained Variance Ratio: $\text{EVR}_k = \frac{\lambda_k}{\sum \lambda_j}$
- **Output Artifacts**:
  - `reports/statistics/pca_report.json`
  - `reports/statistics/pca_loadings.csv`
  - `reports/figures/pca_explained_variance.png`

---

## Practical 7: Classification Models & Evaluation
- **Syllabus Unit**: Unit IV (Supervised Machine Learning)
- **Script**: `scripts/08_train_classifiers.py`
- **Theory**: Multi-class classification comparing non-parametric models on imbalanced tree species data.
- **Algorithms**:
  1. Decision Tree (Gini index, max depth 20)
  2. Random Forest (Ensemble of 200 trees, balanced sub-sampling)
  3. K-Nearest Neighbors ($k=7$, distance-weighted Euclidean metric)
- **Metrics Evaluated**:
  - Accuracy: $\frac{\text{TP} + \text{TN}}{\text{Total}}$
  - Balanced Accuracy: $\frac{1}{C}\sum_{c=1}^C \text{Recall}_c$
  - Macro F1: $\frac{1}{C}\sum_{c=1}^C F_{1, c}$
- **Output Artifacts**:
  - Serialized pipelines: `models/*.joblib`
  - Metrics summaries: `reports/statistics/classification_metrics_summary.csv`
  - Confusion matrices: `reports/figures/confusion_matrix_*.png`

---

## Practical 8: Unsupervised Clustering Analysis
- **Syllabus Unit**: Unit IV (Unsupervised Machine Learning)
- **Script**: `scripts/09_run_clustering.py`
- **Theory**: Spatial grouping of terrain cells without label guidance to discover natural ecological niches.
- **Methods**:
  - K-Means with Elbow Method (Within-Cluster Sum of Squares, WCSS)
  - Silhouette Analysis: $s(i) = \frac{b(i) - a(i)}{\max(a(i), b(i))}$
  - Agglomerative Hierarchical Clustering (Ward linkage)
- **Output Artifacts**:
  - `reports/statistics/cluster_profiles.csv`
  - `reports/figures/kmeans_elbow_curve.png`
  - `reports/figures/kmeans_silhouette_scores.png`

---

## Practical 9: Forest Fires Burned Area Regression
- **Syllabus Unit**: Unit IV (Regression & Modeling)
- **Script**: `scripts/10_train_fires_regression.py`
- **Theory**: Separate continuous task predicting wildfire burned area ($ha$) from weather conditions using the UCI Forest Fires dataset. Log1p transformation mitigates heavy zero-inflation.
- **Formulas / Concepts**:
  - Target: $y = \ln(\text{area} + 1)$
  - Root Mean Squared Error: $\text{RMSE} = \sqrt{\frac{1}{n}\sum (y_i - \hat{y}_i)^2}$
  - Mean Absolute Error: $\text{MAE} = \frac{1}{n}\sum |y_i - \hat{y}_i|$
- **Output Artifacts**:
  - `reports/statistics/forest_fires_regression_results.csv`
  - `reports/figures/regression_true_vs_pred_*.png`

---

## Practical 10: Data Preprocessing Experiments
- **Syllabus Unit**: Unit I & IV (Preprocessing & Transformation)
- **Script**: `scripts/06_preprocessing_experiments.py`
- **Theory**: Comparative empirical assessment of scaling and binning methods.
- **Transformations**:
  1. 1-D Local Average Smoothing: $y_i = \frac{1}{2k+1}\sum_{j=-k}^k x_{i+j}$
  2. Min-Max Normalization: $x_{\text{norm}} = \frac{x - x_{\min}}{x_{\max} - x_{\min}} \in [0, 1]$
  3. Z-Score Standardization: $x_{\text{std}} = \frac{x - \mu}{\sigma} \sim \mathcal{N}(0, 1)$
  4. Quantile Discretization: Partitioning into equal-frequency intervals
- **Output Artifacts**:
  - `reports/statistics/preprocessing_comparison.csv`
  - `reports/practical_evidence/practical10_preprocessing.md`
