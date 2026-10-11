# Practical 10: Data Preprocessing Report
*Generated: 2026-10-11 08:53:15*

## 1. Smoothing
Local 1-D mean smoothing (window=5) applied to continuous features via `GaussianSmoother`
in `python_src/preprocessing.py`. Reduces micro-noise while preserving overall distribution shape.

## 2. Normalisation (Min-Max Scaling)
Scales each feature to [0, 1] using: x' = (x - min) / (max - min).
Fit on training data only. Required for distance-based algorithms (KNN).

## 3. Standardisation (Z-Score)
Scales to mean=0, std=1 using: z = (x - μ) / σ.
Fit on training data only. Required for PCA and regularised models.

## 4. Pearson Correlation
Pearson r measures linear association between two continuous variables.
Formula: r = Σ[(xi - x̄)(yi - ȳ)] / √[Σ(xi - x̄)² × Σ(yi - ȳ)²]

High-correlation pairs (|r| > 0.75): 1 pairs found.

## 5. Chi-Square Feature Selection
χ² tests independence between a feature and the target class.
Non-negative representation required — continuous features min-max scaled to [0,1].
Chi-square is appropriate for categorical or discretised targets.
Top chi-square feature: **Wilderness_Area4** (χ²=25134.3)

## 6. Discretisation
Quantile binning (5 equal-frequency bins) converts continuous features into ordinal bins.
Useful for rule-based systems and reducing impact of extreme outliers.

## 7. Redundancy Analysis
Greedy correlation-based removal: 0 features flagged as redundant (r ≥ 0.90).
Flagged: []