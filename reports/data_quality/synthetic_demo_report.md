# Synthetic Missing-Value Cleaning Experiment Report

## Purpose
This experiment demonstrates the missing-value imputation pipeline on a controlled
teaching copy of the Covertype dataset.  The original source CSV is never modified.

## Experiment Parameters
- Sample size: **10,000 rows**
- Missing values injected: **800** cells
- Injection seed: `2024`
- Columns eligible for injection: ['Elevation', 'Aspect', 'Slope', 'Horizontal_Distance_To_Hydrology', 'Vertical_Distance_To_Hydrology', 'Horizontal_Distance_To_Roadways', 'Hillshade_9am', 'Hillshade_Noon', 'Hillshade_3pm', 'Horizontal_Distance_To_Fire_Points']

## Validation Results
- ✅ **row_count_preserved**: baseline: 10000, cleaned: 10000
- ✅ **injected_count_exact**: expected: 800, actual: 800
- ✅ **zero_missing_after_cleaning**: remaining_missing_cells: 0
- ✅ **target_labels_unchanged**: 

## Imputation Summary
| Column | Median Used | Cells Imputed |
|--------|------------|---------------|
| Elevation | 2997.5 | 76 |
| Aspect | 129.0 | 69 |
| Slope | 13.0 | 74 |
| Horizontal_Distance_To_Hydrology | 218.0 | 72 |
| Vertical_Distance_To_Hydrology | 29.0 | 81 |
| Horizontal_Distance_To_Roadways | 1996.0 | 68 |
| Hillshade_9am | 218.0 | 99 |
| Hillshade_Noon | 226.0 | 69 |
| Hillshade_3pm | 142.0 | 85 |
| Horizontal_Distance_To_Fire_Points | 1708.0 | 107 |

## Conclusion
The imputation pipeline successfully resolved all injected missing values.
Row count and target labels were preserved exactly.
This experiment satisfies the **Practical 2** cleaning demonstration requirement.