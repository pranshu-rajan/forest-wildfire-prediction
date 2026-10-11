"""
Feature schema definitions for the Covertype dataset.

Single source of truth for column names, types, and roles.
All preprocessing pipelines, models, and API validators must import from here.

Covertype dataset (UCI ML Repository):
  - 581,012 rows
  - 55 columns: 54 predictors + Cover_Type
  - No record_id in the source CSV (added synthetically for traceability)
"""

from __future__ import annotations

from typing import Final

# ---------------------------------------------------------------------------
# Column groups
# ---------------------------------------------------------------------------

CONTINUOUS_FEATURES: Final[list[str]] = [
    "Elevation",
    "Aspect",
    "Slope",
    "Horizontal_Distance_To_Hydrology",
    "Vertical_Distance_To_Hydrology",
    "Horizontal_Distance_To_Roadways",
    "Hillshade_9am",
    "Hillshade_Noon",
    "Hillshade_3pm",
    "Horizontal_Distance_To_Fire_Points",
]

WILDERNESS_FEATURES: Final[list[str]] = [
    "Wilderness_Area1",
    "Wilderness_Area2",
    "Wilderness_Area3",
    "Wilderness_Area4",
]

SOIL_FEATURES: Final[list[str]] = [f"Soil_Type{i}" for i in range(1, 41)]

BINARY_FEATURES: Final[list[str]] = WILDERNESS_FEATURES + SOIL_FEATURES

ALL_FEATURES: Final[list[str]] = CONTINUOUS_FEATURES + BINARY_FEATURES

TARGET_COLUMN: Final[str] = "Cover_Type"

# record_id is added for traceability but NEVER used as a predictor
RECORD_ID_COLUMN: Final[str] = "record_id"

# Classes 1-7 inclusive
TARGET_CLASSES: Final[list[int]] = [1, 2, 3, 4, 5, 6, 7]

COVER_TYPE_NAMES: Final[dict[int, str]] = {
    1: "Spruce/Fir",
    2: "Lodgepole Pine",
    3: "Ponderosa Pine",
    4: "Cottonwood/Willow",
    5: "Aspen",
    6: "Douglas-fir",
    7: "Krummholz",
}

WILDERNESS_AREA_NAMES: Final[dict[str, str]] = {
    "Wilderness_Area1": "Rawah",
    "Wilderness_Area2": "Neota",
    "Wilderness_Area3": "Comanche Peak",
    "Wilderness_Area4": "Cache la Poudre",
}

# Expected value ranges for continuous features (for validation)
CONTINUOUS_VALID_RANGES: Final[dict[str, tuple[float, float]]] = {
    "Elevation":                            (1_800, 4_000),   # metres above sea level
    "Aspect":                               (0, 360),          # compass degrees
    "Slope":                                (0, 90),           # degrees
    "Horizontal_Distance_To_Hydrology":     (0, 1_500),        # metres
    "Vertical_Distance_To_Hydrology":       (-200, 700),       # metres (can be negative)
    "Horizontal_Distance_To_Roadways":      (0, 8_000),        # metres
    "Hillshade_9am":                        (0, 255),          # index 0-255
    "Hillshade_Noon":                       (0, 255),
    "Hillshade_3pm":                        (0, 255),
    "Horizontal_Distance_To_Fire_Points":   (0, 8_000),        # metres
}

# Expected dtypes after loading
EXPECTED_DTYPES: Final[dict[str, str]] = {
    **{col: "int64" for col in CONTINUOUS_FEATURES},
    **{col: "int64" for col in BINARY_FEATURES},
    TARGET_COLUMN: "int64",
}

# Total expected predictor count (must not include target or record_id)
N_FEATURES: Final[int] = len(ALL_FEATURES)          # 54
N_CONTINUOUS: Final[int] = len(CONTINUOUS_FEATURES)  # 10
N_WILDERNESS: Final[int] = len(WILDERNESS_FEATURES)  # 4
N_SOIL: Final[int] = len(SOIL_FEATURES)              # 40
N_CLASSES: Final[int] = len(TARGET_CLASSES)          # 7

# Columns present in the raw CSV (no record_id)
RAW_CSV_COLUMNS: Final[list[str]] = ALL_FEATURES + [TARGET_COLUMN]

# ---------------------------------------------------------------------------
# Forest Fires dataset schema (for Practical 9 regression)
# ---------------------------------------------------------------------------

FIRES_CONTINUOUS_FEATURES: Final[list[str]] = [
    "X", "Y", "FFMC", "DMC", "DC", "ISI", "temp", "RH", "wind", "rain",
]
FIRES_CATEGORICAL_FEATURES: Final[list[str]] = ["month", "day"]
FIRES_TARGET: Final[str] = "area"

FIRES_RAW_COLUMNS: Final[list[str]] = (
    FIRES_CATEGORICAL_FEATURES
    + ["X", "Y", "FFMC", "DMC", "DC", "ISI", "temp", "RH", "wind", "rain"]
    + [FIRES_TARGET]
)
