# Tableau Dashboard Construction Guide
## Forest Cover Type Prediction & Wildfire-Risk Analysis

This guide provides step-by-step blueprints for building the 3 production dashboards in Tableau Desktop / Tableau Cloud using the flat files in `exports/tableau/` or the PostgreSQL views in `database/views.sql`.

---

## Dashboard 1 — Executive Forest Cover Overview

### Business Objective
Provide forestry executives and ecologists with an immediate high-level summary of Roosevelt National Forest tree distributions, class prevalence, and species dominance.

### Key Performance Indicator (KPI) Cards (Top Row)
1. **Total Forest Observations**: `581,012` (Card showing total recorded 30m × 30m grid plots)
2. **Dominant Species**: `Lodgepole Pine` (48.76% of total forest cover)
3. **Secondary Species**: `Spruce/Fir` (36.46% of total forest cover)
4. **Minority / Threatened Species**: `Cottonwood/Willow` (0.47% prevalence)
5. **Class Imbalance Ratio**: `103:1` (Max class / Min class ratio highlighting severe imbalance)

### Visualizations
1. **Species Distribution Donut / Treemap**:
   - Dimension: `cover_name`
   - Measure: `count` and `% of Total`
   - Tooltip: Total count, percentage, scientific name, and primary elevation band.
2. **Wilderness Area Distribution (Stacked Horizontal Bar Chart)**:
   - Rows: `wilderness_area` (Rawah, Neota, Comanche Peak, Cache la Poudre)
   - Columns: `observation_count`
   - Color: `cover_name` (consistent 7-color qualitative palette)
3. **Interactive Filters**:
   - Multi-select dropdown: `Cover Type`
   - Single-select radio: `Wilderness Area`
   - Slider: `Elevation Range (meters)`

---

## Dashboard 2 — Terrain and Cover-Type Analysis

### Business Objective
Analyze the multidimensional topographic drivers (elevation, slope, hydrology, and solar aspect) that govern tree species distribution.

### Visualizations
1. **Elevation Boxplots & Density Bands**:
   - X-Axis: `cover_name`
   - Y-Axis: `Elevation (meters)`
   - Visual: Boxplot showing median, IQR, whiskers, and outlier thresholds.
   - Ecological takeaway: Spruce/Fir and Krummholz dominate subalpine (>3,000m), whereas Cottonwood/Willow thrives in riparian lowlands (<2,300m).
2. **Slope vs Distance to Hydrology Scatter / Hexbin Plot**:
   - X-Axis: `Horizontal_Distance_To_Hydrology`
   - Y-Axis: `Slope (degrees)`
   - Color: `cover_name`
   - Detail: 30m cell sample from `exports/tableau/covtype_tableau_sample.csv`
3. **Solar Exposure Radar / Circular Hillshade Profile**:
   - Visual: Dual comparison of `Hillshade_9am` vs `Hillshade_3pm` across aspect angles (0°–360°).
   - Tooltip: Hillshade intensity index [0–255] and slope gradient.
4. **Interactive Filters**:
   - Range slider: `Slope (0° to 60°)`
   - Dropdown: `Soil Type Family`
   - Highlight Action: Selecting a cover type highlights corresponding points across all three charts.

---

## Dashboard 3 — Model Performance and Risk-Screening Analytics

### Business Objective
Evaluate classification model accuracy across imbalanced classes and present exploratory topographic wildfire risk screening metrics.

### Visualizations
1. **Model Comparison Grouped Bar Chart**:
   - Columns: `Model Name` (Decision Tree, Random Forest, K-Nearest Neighbors)
   - Rows: Metric score [0.0 to 1.0]
   - Measures: `Accuracy`, `Balanced Accuracy`, `Macro F1`, `Weighted F1`
   - Observation: Random Forest achieves highest overall accuracy and balanced F1 score.
2. **Normalized Confusion Matrix Heatmap**:
   - Rows: `True Cover Type`
   - Columns: `Predicted Cover Type`
   - Color: % Correct Prediction (Green-Blue sequential gradient)
   - Tooltip: Cell counts, true positive rate, and frequent misclassifications (e.g. Class 1 Spruce/Fir vs Class 2 Lodgepole Pine).
3. **Topographic Wildfire Risk Screening Summary**:
   - Data Source: `exports/tableau/wildfire_screening_aggregates.csv`
   - Visual: Trellis Bar Chart showing `Mean Screening Risk Score` by `Wilderness Area` and `Cover Type`.
   - Color: Risk Tier (`High Screening Risk` = Burnt Orange, `Moderate` = Amber, `Low` = Forest Green).
   - **Prominent Disclaimer Banner**:
     > *"This screening score is an exploratory topographic index combining proximity to fire points, slope steepness, and solar radiation. It does NOT represent calibrated empirical fire ignition probability or weather-driven fire behavior."*

---

## Interactivity & Cross-Dashboard Navigation

1. **Top Navigation Bar**: Action buttons linking between Dashboard 1 (Overview), Dashboard 2 (Terrain), and Dashboard 3 (Models & Screening).
2. **Filter Inheritance**: Global filters for Wilderness Area apply seamlessly across Dashboards 1 and 2.
3. **Hover Tooltips**: Formatted cleanly with proper unit labels (`m`, `°`, `%`) and bold headers.
