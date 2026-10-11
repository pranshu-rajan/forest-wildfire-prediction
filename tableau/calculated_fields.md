# Tableau Calculated Fields & Formulas Reference

Use these formulas when creating calculated fields in Tableau Desktop.

---

## 1. Executive KPIs & Cover Type Labels

### `Cover Type Label`
```tableau
CASE [Cover_Type]
    WHEN 1 THEN "Spruce/Fir"
    WHEN 2 THEN "Lodgepole Pine"
    WHEN 3 THEN "Ponderosa Pine"
    WHEN 4 THEN "Cottonwood/Willow"
    WHEN 5 THEN "Aspen"
    WHEN 6 THEN "Douglas-fir"
    WHEN 7 THEN "Krummholz"
    ELSE "Unknown"
END
```

### `% of Total Observations`
```tableau
COUNT([Elevation]) / TOTAL(COUNT([Elevation]))
```

### `Class Imbalance Flag`
```tableau
IF [% of Total Observations] < 0.05 THEN "Minority Class (<5%)"
ELSEIF [% of Total Observations] > 0.30 THEN "Dominant Class (>30%)"
ELSE "Intermediate Class"
END
```

---

## 2. Terrain & Topographic Indices

### `Elevation Band (500m Intervals)`
```tableau
IF [Elevation] < 2000 THEN "< 2,000m (Lowland)"
ELSEIF [Elevation] < 2500 THEN "2,000m - 2,499m (Montane)"
ELSEIF [Elevation] < 3000 THEN "2,500m - 2,999m (Subalpine Lower)"
ELSEIF [Elevation] < 3500 THEN "3,000m - 3,499m (Subalpine Upper)"
ELSE ">= 3,500m (Alpine / Tree Line)"
END
```

### `Slope Category`
```tableau
IF [Slope] < 10 THEN "Gentle (0°-9°)"
ELSEIF [Slope] < 25 THEN "Moderate (10°-24°)"
ELSEIF [Slope] < 40 THEN "Steep (25°-39°)"
ELSE "Very Steep (>= 40°)"
END
```

### `Solar Exposure Differential`
```tableau
[Hillshade_Noon] - [Hillshade_9am]
```

---

## 3. Topographic Wildfire Screening Risk Metric

### `Normalized Proximity Factor`
```tableau
1.0 - (MIN([Horizontal_Distance_To_Fire_Points], 7000) / 7000.0)
```

### `Normalized Slope Hazard`
```tableau
MIN([Slope], 60) / 60.0
```

### `Topographic Screening Risk Score`
```tableau
ROUND(
    (0.40 * [Normalized Proximity Factor] +
     0.35 * [Normalized Slope Hazard] +
     0.25 * (MIN([Hillshade_Noon], 255) / 255.0)
    ) * 100, 
    1
)
```

### `Risk Screening Tier`
```tableau
IF [Topographic Screening Risk Score] >= 65 THEN "High Screening Risk"
ELSEIF [Topographic Screening Risk Score] >= 35 THEN "Moderate Screening Risk"
ELSE "Low Screening Risk"
END
```

---

## 4. Model Performance Calculations

### `Prediction Accuracy Flag`
```tableau
IF [true_cover_type] = [predicted_cover_type] THEN 1 ELSE 0 END
```

### `Overall Accuracy (%)`
```tableau
SUM([Prediction Accuracy Flag]) / COUNT([Prediction Accuracy Flag]) * 100
```
