# Tableau User & Implementation Guide
## Forest Cover Type Prediction & Wildfire-Risk Analysis

---

## 1. Overview
The project includes pre-aggregated, validated analytical tables in `exports/tableau/` specifically structured for Tableau Desktop / Tableau Cloud dashboards.

The three dashboards are:
1. **Executive Forest Cover Overview**
2. **Terrain and Cover-Type Analysis**
3. **Model Performance and Risk-Screening Analytics**

---

## 2. Step-by-Step Dashboard Setup

### Dashboard 1: Executive Overview
- **Data Source**: `exports/tableau/cover_distribution.csv` and `wilderness_cover_summary.csv`
- **Steps**:
  1. Drag `cover_name` to Rows, `count` to Columns -> Bar Chart.
  2. Create Calculated Field `% of Total` = `SUM([count]) / TOTAL(SUM([count]))`.
  3. Drag `% of Total` to Label.
  4. Build Stacked Bar Chart for `wilderness_area` × `cover_name`.
  5. Add Top KPI Cards using Big Number metric tiles.

### Dashboard 2: Terrain Analysis
- **Data Source**: `exports/tableau/terrain_summary_by_cover_type.csv` and `covtype_tableau_sample.csv`
- **Steps**:
  1. Boxplot: Drag `Elevation` to Rows, `cover_name` to Columns. Set Mark Type to Boxplot.
  2. Scatter: `Horizontal_Distance_To_Hydrology` (Columns) vs `Slope` (Rows), color by `cover_name`.
  3. Solar Aspect: Dual axis comparison of `Hillshade_9am` vs `Hillshade_3pm`.

### Dashboard 3: Model Evaluation & Wildfire Screening
- **Data Source**: `exports/tableau/classification_metrics.csv` and `wildfire_screening_aggregates.csv`
- **Steps**:
  1. Multi-metric Bar Chart comparing Decision Tree, Random Forest, and KNN across Accuracy, Balanced Accuracy, and Macro F1.
  2. Wildfire Risk Screening: Drag `wilderness_area` and `cover_name` to Rows, `mean_screening_risk_score` to Columns.
  3. Color by `risk_tier` (`High Screening Risk` = Orange, `Moderate` = Amber, `Low` = Green).
  4. Add the prominent disclaimer text banner explaining that the score is a topographic hazard metric, not an empirical fire probability.

---

## 3. Visual Formatting Standards
- **Font**: Tableau Medium or Inter.
- **Palette**: Qualitative 7-color palette mapped identically across all sheets for the 7 Cover Types.
- **Layout**: 1440px × 900px desktop fixed layout with responsive containers.
