# Practical 3: Descriptive Statistics Report
*Generated: 2026-10-11 08:53:04*

## Purpose
This report fulfils the Practical 3 requirement to compute and interpret
descriptive statistics for the Covertype dataset's continuous features.


## Statistical Formulas

| Statistic | Formula |
|-----------|---------|
| Mean | $\bar{x} = \frac{1}{n}\sum_{i=1}^{n} x_i$ |
| Median | Middle value of sorted data |
| Mode | Most frequent value |
| Midrange | $\frac{x_{\min} + x_{\max}}{2}$ |
| Range | $x_{\max} - x_{\min}$ |
| Q1 | 25th percentile |
| Q3 | 75th percentile |
| IQR | $Q_3 - Q_1$ |
| Variance | $s^2 = \frac{1}{n-1}\sum_{i=1}^{n}(x_i - \bar{x})^2$ |
| Std Dev | $s = \sqrt{s^2}$ |
| Skewness | $\frac{n}{(n-1)(n-2)}\sum\left(\frac{x_i-\bar{x}}{s}\right)^3$ |


## Results Table

| feature                            |   count |      mean |   median |   mode |   midrange |   min |   max |   range |   q1 |   q3 |   iqr |        variance |   std_dev |   skewness |   kurtosis |
|:-----------------------------------|--------:|----------:|---------:|-------:|-----------:|------:|------:|--------:|-----:|-----:|------:|----------------:|----------:|-----------:|-----------:|
| Elevation                          |  581012 | 2959.37   |     2996 |   2968 |     2858.5 |  1859 |  3858 |    1999 | 2809 | 3163 |   354 | 78391.5         |  279.985  |    -0.8176 |     0.7493 |
| Aspect                             |  581012 |  155.657  |      127 |     45 |      180   |     0 |   360 |     360 |   58 |  260 |   202 | 12524.7         |  111.914  |     0.4026 |    -1.2202 |
| Slope                              |  581012 |   14.1037 |       13 |     11 |       33   |     0 |    66 |      66 |    9 |   18 |     9 |    56.0738      |    7.4882 |     0.7893 |     0.5812 |
| Horizontal_Distance_To_Hydrology   |  581012 |  269.428  |      218 |     30 |      698.5 |     0 |  1397 |    1397 |  108 |  384 |   276 | 45177.2         |  212.549  |     1.1404 |     1.3662 |
| Vertical_Distance_To_Hydrology     |  581012 |   46.4189 |       30 |      0 |      214   |  -173 |   601 |     774 |    7 |   69 |    62 |  3398.33        |   58.2952 |     1.7902 |     5.2503 |
| Horizontal_Distance_To_Roadways    |  581012 | 2350.15   |     1997 |    150 |     3558.5 |     0 |  7117 |    7117 | 1106 | 3328 |  2222 |     2.43128e+06 | 1559.25   |     0.7137 |    -0.3837 |
| Hillshade_9am                      |  581012 |  212.146  |      218 |    226 |      127   |     0 |   254 |     254 |  198 |  231 |    33 |   716.627       |   26.7699 |    -1.1811 |     1.8755 |
| Hillshade_Noon                     |  581012 |  223.319  |      226 |    228 |      127   |     0 |   254 |     254 |  213 |  237 |    24 |   390.801       |   19.7687 |    -1.0631 |     2.0662 |
| Hillshade_3pm                      |  581012 |  142.528  |      143 |    143 |      127   |     0 |   254 |     254 |  119 |  168 |    49 |  1464.94        |   38.2745 |    -0.2771 |     0.3984 |
| Horizontal_Distance_To_Fire_Points |  581012 | 1980.29   |     1710 |    618 |     3586.5 |     0 |  7173 |    7173 | 1024 | 2550 |  1526 |     1.75349e+06 | 1324.2    |     1.2886 |     1.6458 |

## Five-Number Summary

| feature                            |   min |   q1 |   median |   q3 |   max |
|:-----------------------------------|------:|-----:|---------:|-----:|------:|
| Elevation                          |  1859 | 2809 |     2996 | 3163 |  3858 |
| Aspect                             |     0 |   58 |      127 |  260 |   360 |
| Slope                              |     0 |    9 |       13 |   18 |    66 |
| Horizontal_Distance_To_Hydrology   |     0 |  108 |      218 |  384 |  1397 |
| Vertical_Distance_To_Hydrology     |  -173 |    7 |       30 |   69 |   601 |
| Horizontal_Distance_To_Roadways    |     0 | 1106 |     1997 | 3328 |  7117 |
| Hillshade_9am                      |     0 |  198 |      218 |  231 |   254 |
| Hillshade_Noon                     |     0 |  213 |      226 |  237 |   254 |
| Hillshade_3pm                      |     0 |  119 |      143 |  168 |   254 |
| Horizontal_Distance_To_Fire_Points |     0 | 1024 |     1710 | 2550 |  7173 |

## Sample Interpretation: Elevation
- **Mean:** 2,959.4 m — the average elevation across all 581,012 observations.
- **Median:** 2,996.0 m — 50% of observations lie below this elevation.
- **Std Dev:** 280.0 m — moderate spread indicating varied terrain.
- **IQR:** 354.0 m — the middle 50% spans 354 metres.
- **Skewness:** -0.818 — moderately skewed.