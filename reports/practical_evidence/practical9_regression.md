# Practical 9: Forest Fires Regression Report
*Generated: 2026-10-11 09:18:18*

## Dataset Overview
- **Dataset**: UCI Forest Fires (Montesinho Natural Park, Portugal)
- **Observations**: 517
- **Zero-Area Fires**: 247
- **Target Transformation**: `y = log1p(area)` to handle extreme right skewness

## Regression Model Evaluation (Test Set)
| model             |   mae_log |   rmse_log |   r2_log |   mae_original_scale |   rmse_original_scale |
|:------------------|----------:|-----------:|---------:|---------------------:|----------------------:|
| Linear Regression |    1.1992 |     1.4852 |  -0.0036 |              19.8295 |               109.901 |
| Ridge Regression  |    1.1991 |     1.4851 |  -0.0034 |              19.8291 |               109.901 |
| Decision Tree     |    1.3146 |     1.7013 |  -0.3169 |              22.0815 |               110.452 |
| Random Forest     |    1.22   |     1.5169 |  -0.047  |              19.9604 |               109.956 |

## Best Performing Model: Ridge Regression
- Evaluated on both log-transformed scale (MAE, RMSE, R²) and raw hectare scale.
- Feature set includes meteorological predictors: FFMC, DMC, DC, ISI, temp, RH, wind, rain, plus encoded month/day.

## Academic & Methodological Notes
Forest fire burned area is notoriously challenging to predict due to meteorological non-linearities and high percentage of small, quickly contained fires (zero-area recorded). The log1p transformation stabilizes variance and minimizes extreme prediction penalties.
