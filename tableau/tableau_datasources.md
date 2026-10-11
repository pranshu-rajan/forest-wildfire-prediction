# Tableau Data Sources & Database Views

This document outlines data source specifications for connecting Tableau to flat files or live PostgreSQL.

---

## Data Sources Architecture

```
                    +------------------------------+
                    |      PostgreSQL Database     |
                    | (analytics.v_cover_type_...) |
                    +--------------+---------------+
                                   | (Live connection)
                                   v
+-----------------------+     +----+-------------------+
|  Flat CSV Extracts    | --> |   Tableau Desktop      |
|  (exports/tableau/)   |     |   3 Built Dashboards   |
+-----------------------+     +------------------------+
```

---

## Flat CSV Extracts (`exports/tableau/`)

When working offline or without a running PostgreSQL instance, import these files:

1. `terrain_summary_by_cover_type.csv`: Means, medians, standard deviations for all 10 terrain metrics grouped by cover class.
2. `wilderness_cover_summary.csv`: Cross-tabulation of Wilderness Areas vs Cover Types.
3. `wildfire_screening_aggregates.csv`: Topographic screening scores and tiers.
4. `cover_distribution.csv`: Class frequencies and percentages.
5. `classification_metrics.csv`: Performance metrics across models.
6. `covtype_tableau_sample.csv`: 20,000-row representative sample for granular scatter, boxplot, and density distributions.
7. `data_dictionary.csv`: Field types, valid ranges, and domain descriptions.

---

## Live PostgreSQL Connection

When connected to PostgreSQL:
- **Server**: `localhost` (or cloud host)
- **Port**: `5432`
- **Database**: `covtype_db`
- **Schemas**:
  - `curated`: `forest_cover` table
  - `analytics`:
    - `v_cover_type_summary` (Dashboard 1)
    - `v_terrain_profile` (Dashboard 2)
    - `v_wildfire_screening_risk` (Dashboard 3)
