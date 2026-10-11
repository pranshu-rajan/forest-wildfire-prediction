"""
Pytest fixtures for fast, isolated unit testing without loading the full 580k dataset.
"""

from __future__ import annotations

import sys
from pathlib import Path

# Ensure workspace root is in sys.path
root_dir = Path(__file__).parent.parent
if str(root_dir) not in sys.path:
    sys.path.insert(0, str(root_dir))

import numpy as np
import pandas as pd
import pytest

from python_src.schemas import (
    ALL_FEATURES,
    CONTINUOUS_FEATURES,
    SOIL_FEATURES,
    TARGET_COLUMN,
    WILDERNESS_FEATURES,
)


@pytest.fixture
def synthetic_covtype_df() -> pd.DataFrame:
    """Generate a realistic small synthetic DataFrame (200 rows) matching the Covertype schema."""
    rng = np.random.default_rng(42)
    n = 200

    data = {}
    # Continuous features
    for col in CONTINUOUS_FEATURES:
        data[col] = rng.integers(low=10, high=3000, size=n)

    # Wilderness Areas (mutually exclusive one-hot)
    wa_choice = rng.integers(0, 4, size=n)
    for i, col in enumerate(WILDERNESS_FEATURES):
        data[col] = (wa_choice == i).astype(int)

    # Soil Types (mutually exclusive one-hot)
    soil_choice = rng.integers(0, 40, size=n)
    for i, col in enumerate(SOIL_FEATURES):
        data[col] = (soil_choice == i).astype(int)

    # Target (1 to 7)
    data[TARGET_COLUMN] = rng.integers(1, 8, size=n)

    df = pd.DataFrame(data)
    return df


@pytest.fixture
def sample_feature_dict() -> dict:
    """A valid single-sample feature dictionary for testing prediction endpoints."""
    sample = {}
    for col in CONTINUOUS_FEATURES:
        sample[col] = 1500
    for i, col in enumerate(WILDERNESS_FEATURES):
        sample[col] = 1 if i == 0 else 0
    for i, col in enumerate(SOIL_FEATURES):
        sample[col] = 1 if i == 9 else 0
    return sample
