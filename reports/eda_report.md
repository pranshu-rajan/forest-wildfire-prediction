# Exploratory Data Analysis Report
*Generated: 2026-10-11 08:52:48*

## Dataset Overview
- **Rows:** 581,012
- **Columns:** 56
- **Continuous features:** 10
- **Binary features:** 44
- **Total missing cells:** 0
- **Duplicate rows:** 0
- **Memory usage:** 260.29 MB

## Class Distribution (Cover_Type)
| Class | Name | Count | % |
|-------|------|-------|---|
| 1 | Spruce/Fir | 211,840 | 36.46% |
| 2 | Lodgepole Pine | 283,301 | 48.76% |
| 3 | Ponderosa Pine | 35,754 | 6.15% |
| 4 | Cottonwood/Willow | 2,747 | 0.47% |
| 5 | Aspen | 9,493 | 1.63% |
| 6 | Douglas-fir | 17,367 | 2.99% |
| 7 | Krummholz | 20,510 | 3.53% |

## Descriptive Statistics (Continuous Features)

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

## Key Observations
- The dataset has **no missing values** in the original source.
- Class imbalance is present: classes 1 (Spruce/Fir) and 2 (Lodgepole Pine) dominate.
- Hillshade features (9am, Noon, 3pm) show moderate inter-correlation.
- Many soil type columns are sparse (< 1% activation).

## Figures Generated
- `reports/figures/class_distribution_bar.png`
- `reports/figures/class_distribution_pie.png`
- `reports/figures/continuous_distributions.png`
- `reports/figures/boxplots_by_cover_type.png`
- `reports/figures/correlation_heatmap.png`
- `reports/figures/scatter_elevation_vs_hydrology.png`
- `reports/figures/wilderness_area_distribution.png`
- `reports/figures/soil_type_frequency.png`
- `reports/figures/treemap_cover_type.png`
- `reports/figures/radial_cover_distribution.png`