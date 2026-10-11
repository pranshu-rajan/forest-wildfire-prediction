# Practical 6b: Feature Selection and PCA Report
*Generated: 2026-10-11 08:55:18*

## Feature Ranking Summary
- Total features: 54
- After variance threshold: 47
- Removed (zero-variance): ['Soil_Type7', 'Soil_Type8', 'Soil_Type14', 'Soil_Type15', 'Soil_Type25', 'Soil_Type36', 'Soil_Type37']

### Top 10 Features by Mean Rank
| feature                         |   f_score |   f_rank |   chi2_score |   chi2_rank |   mutual_info |   mi_rank |   mean_rank |
|:--------------------------------|----------:|---------:|-------------:|------------:|--------------:|----------:|------------:|
| Wilderness_Area4                | 10024.6   |        2 |    25574.3   |           1 |      0.143509 |         2 |     1.66667 |
| Soil_Type10                     |  2328.95  |        3 |    10310.3   |           2 |      0.062013 |         6 |     3.66667 |
| Soil_Type4                      |  1166.33  |        4 |     6006.55  |           3 |      0.026838 |        13 |     6.66667 |
| Soil_Type39                     |  1128.79  |        5 |     5813.14  |           4 |      0.027397 |        12 |     7       |
| Soil_Type38                     |  1029.89  |        6 |     5355.77  |           5 |      0.029087 |        11 |     7.33333 |
| Elevation                       | 13321.1   |        1 |     1115.77  |          20 |      0.456891 |         1 |     7.33333 |
| Wilderness_Area1                |   895.503 |        8 |     2669.53  |          11 |      0.073774 |         4 |     7.66667 |
| Soil_Type2                      |   888.578 |        9 |     4755.53  |           7 |      0.024105 |        15 |    10.3333  |
| Soil_Type3                      |   921.943 |        7 |     4939.62  |           6 |      0.016984 |        21 |    11.3333  |
| Horizontal_Distance_To_Roadways |   866.004 |       10 |      684.145 |          23 |      0.084274 |         3 |    12       |

## PCA Results (Continuous Features)
- Input features: 10 continuous features
- Components retained: 8 (for 96.9% variance)
- Components for 90% variance: 7
- Components for 95% variance: 8

## PCA Limitations
- PCA is sensitive to feature scale — standardisation is mandatory first.
- PCA assumes linear relationships; non-linear structure may not be captured.
- Interpretability is reduced: each PC is a linear combination of all original features.
- The curse of dimensionality: with 54 features, distance-based methods can degrade.
  PCA mitigates this for the continuous subspace but cannot resolve binary feature sparsity.
