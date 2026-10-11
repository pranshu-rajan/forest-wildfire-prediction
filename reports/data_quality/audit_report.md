# Data Audit Report
*Generated: 2026-10-11 08:51:25*

## Source Manifest
- **File:** C:\Users\pranshu\Desktop\forest-cover-wildfire\data\raw\covtype.csv
- **SHA-256:** `ea35ca6820fcbe0bdc6707e9ed31e11a9de84f07d88da73b511c737383c271a6`
- **Rows:** 581,012
- **Columns:** 56
- **Ingested at:** 2026-10-11T03:21:24.218348+00:00

## Validation Summary
- Total checks: 24
- Passed: 22
- Fatal failures: 0
- Warnings: 2

## Validation Checks
| Check | Passed | Severity | Detail |
|-------|--------|----------|--------|
| file_exists | ✅ | FATAL | 'C:\Users\pranshu\Desktop\forest-cover-wildfire\data\raw\covtype.csv' exists |
| expected_columns_present | ✅ | FATAL | All 55 expected columns present. |
| no_extra_columns | ✅ | WARNING | No unexpected columns. |
| row_count | ✅ | FATAL | 581,012 rows found. |
| feature_column_count | ✅ | FATAL | Expected 54 feature columns, found 54. |
| all_columns_numeric | ✅ | FATAL | All columns are numeric. |
| no_missing_values | ✅ | WARNING | Total missing cells: 0 |
| no_exact_duplicates | ✅ | WARNING | Exact duplicate rows (excluding record_id): 0 |
| target_labels_valid | ✅ | FATAL | All target labels in {1..7}. |
| range_Elevation | ✅ | WARNING | Elevation: [1859, 3858], 0 below 1800, 0 above 4000. |
| range_Aspect | ✅ | WARNING | Aspect: [0, 360], 0 below 0, 0 above 360. |
| range_Slope | ✅ | WARNING | Slope: [0, 66], 0 below 0, 0 above 90. |
| range_Horizontal_Distance_To_Hydrology | ✅ | WARNING | Horizontal_Distance_To_Hydrology: [0, 1397], 0 below 0, 0 above 1500. |
| range_Vertical_Distance_To_Hydrology | ✅ | WARNING | Vertical_Distance_To_Hydrology: [-173, 601], 0 below -200, 0 above 700. |
| range_Horizontal_Distance_To_Roadways | ✅ | WARNING | Horizontal_Distance_To_Roadways: [0, 7117], 0 below 0, 0 above 8000. |
| range_Hillshade_9am | ✅ | WARNING | Hillshade_9am: [0, 254], 0 below 0, 0 above 255. |
| range_Hillshade_Noon | ✅ | WARNING | Hillshade_Noon: [0, 254], 0 below 0, 0 above 255. |
| range_Hillshade_3pm | ✅ | WARNING | Hillshade_3pm: [0, 254], 0 below 0, 0 above 255. |
| range_Horizontal_Distance_To_Fire_Points | ✅ | WARNING | Horizontal_Distance_To_Fire_Points: [0, 7173], 0 below 0, 0 above 8000. |
| binary_features_valid | ✅ | FATAL | All binary indicators contain only 0/1. |
| wilderness_onehot_integrity | ✅ | WARNING | Rows where wilderness area sum ≠ 1: 0 |
| soil_type_nonzero_per_row | ✅ | WARNING | Rows with no active soil type: 0 |
| sparse_soil_columns | ⚠️ | WARNING | 21 soil columns with <1% activation: ['Soil_Type1', 'Soil_Type3', 'Soil_Type5', 'Soil_Type7', 'Soil_ |
| class_imbalance | ⚠️ | WARNING | Imbalance ratio (majority/minority): 103.1x. Dist: {1: 211840, 2: 283301, 3: 35754, 4: 2747, 5: 9493 |

## Cleaning Operations
| Operation | Rows In | Rows Out | Rows Affected | Detail |
|-----------|---------|----------|---------------|--------|