# Practical 7: Classification Report
*Generated: 2026-10-11 08:59:46*

## Models Trained
- Decision Tree (max_depth=20, balanced class weights)
- Random Forest (200 trees, balanced class weights)
- K-Nearest Neighbors (k=7, distance weighting)

## Test Set Results
| model         |   accuracy |   balanced_accuracy |   macro_f1 |   weighted_f1 |   train_time_s |   inference_time_s |
|:--------------|-----------:|--------------------:|-----------:|--------------:|---------------:|-------------------:|
| Decision Tree |     0.8658 |              0.8971 |     0.7939 |        0.8715 |           7.29 |             0.071  |
| Random Forest |     0.9351 |              0.9402 |     0.9059 |        0.9354 |          64.42 |             2.1683 |
| KNN           |     0.9312 |              0.8675 |     0.8804 |        0.931  |           1.3  |           119.353  |

## Cross-Validation Results (50k-sample subset, 5-fold)
| model         |   cv_folds |   cv_accuracy_mean |   cv_accuracy_std |   cv_balanced_accuracy_mean |   cv_macro_f1_mean |   cv_weighted_f1_mean |
|:--------------|-----------:|-------------------:|------------------:|----------------------------:|-------------------:|----------------------:|
| Decision Tree |          5 |             0.7679 |            0.0041 |                      0.7774 |             0.6644 |                0.7758 |
| Random Forest |          5 |             0.8394 |            0.0042 |                      0.8339 |             0.7806 |                0.8409 |
| KNN           |          5 |             0.8414 |            0.0029 |                      0.701  |             0.7249 |                0.8399 |

## Best Model: Random Forest
- Test Accuracy: **0.9351**
- Balanced Accuracy: **0.9402**
- Macro F1: **0.9059**

## Notes on Class Imbalance
The Covertype dataset has significant class imbalance (classes 1 and 2 dominate).
Balanced class weights were used in tree-based models. Balanced accuracy provides
a fairer evaluation metric than plain accuracy for imbalanced datasets.
