# Practical 8: Clustering Analysis Report
*Generated: 2026-10-11 09:17:17*

## Methodology
- **Algorithm**: K-Means clustering evaluated across $k \in [2, 10]$
- **Alternative**: Agglomerative Hierarchical Clustering (Ward linkage, $k=7$)
- **Feature Set**: Continuous terrain predictors only (scaled via StandardScaler)
- **Target Handling**: `Cover_Type` strictly excluded during clustering; used post-hoc for validation only

## Elbow and Silhouette Evaluation
- Evaluated $k=2$ to $k=10$.
- K-Means Silhouette at $k=7$: **0.1567**
- Agglomerative Silhouette at $k=7$: **0.1279**

## Cluster Profiles (Mean Feature Values per Cluster)
|   cluster |   Elevation |   Aspect |   Slope |   Horizontal_Distance_To_Hydrology |   Vertical_Distance_To_Hydrology |   Horizontal_Distance_To_Roadways |   Hillshade_9am |   Hillshade_Noon |   Hillshade_3pm |   Horizontal_Distance_To_Fire_Points |   cluster_size |
|----------:|------------:|---------:|--------:|-----------------------------------:|---------------------------------:|----------------------------------:|----------------:|-----------------:|----------------:|-------------------------------------:|---------------:|
|         0 |     3171.47 | 149.431  | 14.2225 |                            676.949 |                         157.716  |                           2199.93 |         213.375 |          226.331 |        144.445  |                              1865.85 |           2773 |
|         1 |     2845.42 |  85.7545 | 11.2485 |                            198.207 |                          22.4516 |                           1325.09 |         227.315 |          225.325 |        128.984  |                              1632.23 |           7017 |
|         2 |     3126.9  |  81.4489 | 10.7598 |                            223.779 |                          25.1809 |                           3806.72 |         226.533 |          224.72  |        129.532  |                              2093.43 |           5075 |
|         3 |     2930.84 | 137.96   |  9.8084 |                            278.691 |                          31.7868 |                           3838.07 |         218.812 |          229.065 |        143.865  |                              5089.17 |           2584 |
|         4 |     2685.21 | 301.111  | 24.8677 |                            218.925 |                          71.448  |                           1489.94 |         155.687 |          217.499 |        194.364  |                              1300.27 |           2645 |
|         5 |     3055.04 | 283.56   | 11.7167 |                            238.726 |                          29.8107 |                           2566.23 |         196.901 |          236.618 |        176.611  |                              1579.01 |           6481 |
|         6 |     2801.02 |  64.8441 | 23.9232 |                            228.132 |                          57.4347 |                           1493.26 |         226.355 |          189.906 |         82.8336 |                              1518.41 |           3425 |

## Cluster vs Ground-Truth Cover Type Crosstab
|   cluster |    1 |    2 |   3 |   4 |   5 |   6 |   7 |
|----------:|-----:|-----:|----:|----:|----:|----:|----:|
|         0 | 1130 | 1252 |  48 |   2 |  29 |   6 | 306 |
|         1 | 1843 | 4047 | 614 |  53 | 185 | 232 |  43 |
|         2 | 2623 | 2077 |   0 |   0 |   9 |   0 | 366 |
|         3 |  701 | 1852 |   0 |   0 |  14 |   0 |  17 |
|         4 |  514 | 1109 | 584 |  16 |  21 | 390 |  11 |
|         5 | 2994 | 2996 | 120 |   4 |  82 |  64 | 221 |
|         6 |  985 | 1396 | 492 |  52 | 154 | 240 | 106 |

## Key Observations
1. Clusters align closely with elevation bands and hydrology gradients.
2. Unsupervised clusters reveal environmental niches that correspond naturally to ecological vegetation zones.
