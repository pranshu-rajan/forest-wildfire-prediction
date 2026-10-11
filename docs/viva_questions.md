# Comprehensive Viva Voce Questions & Answers
## Forest Cover Type Prediction & Wildfire-Risk Analysis

---

### Q1: Why is missing-value imputation demonstrated on a synthetic dataset instead of the original Covertype dataset?
**Answer**:
The original USFS Forest Covertype dataset (581,012 observations) contains zero missing values across all 55 attributes, as verified by cryptographic SHA-256 auditing. To satisfy the academic requirements of **Practical 2** (Data Cleaning & Imputation) without corrupting or misrepresenting the original benchmark dataset, a controlled 10,000-row sample was drawn. Exactly 800 missing cells were injected solely into continuous predictor columns (never into target or one-hot features). Median imputation was then performed and validated, proving the pipeline's effectiveness while preserving raw data integrity.

---

### Q2: Why did you flag outliers using IQR and Z-scores instead of deleting them?
**Answer**:
In environmental and spatial datasets, extreme values often represent real, ecologically valid landscape features rather than measurement errors. For example:
- Elevations above 3,500m represent alpine Krummholz tree lines.
- Slopes above 45° represent steep canyon cliff sides.
- Roadway distances above 5,000m represent remote interior wilderness.
Deleting these rows would distort natural class distributions and destroy the spatial signatures of rare species. Therefore, Tukey's IQR ($1.5 \times \text{IQR}$) and Z-scores ($|z| > 3$) were computed to flag outliers for awareness, preserving the complete 581k dataset for downstream modeling.

---

### Q3: How do you prevent data leakage in your preprocessing and modeling pipeline?
**Answer**:
We enforced five non-negotiable anti-leakage principles:
1. **Temporal/Stratified Split First**: Partitioning into 80% train and 20% test is executed before any feature scaling, normalization, or dimensionality reduction.
2. **Fit-Transform Isolation**: Transformers (`StandardScaler`, `MinMaxScaler`, `PCA`, `KBinsDiscretizer`) call `.fit()` strictly on the training set, and only `.transform()` on the test set.
3. **No Record ID Features**: `record_id` is generated as an audit tracker and strictly stripped before model ingestion.
4. **Target Isolation**: The target `Cover_Type` is never provided to unsupervised PCA or K-Means clustering.
5. **Exact Split Indices Persisted**: `models/split_indices.json` stores test and train index arrays for identical cross-platform validation in KNIME and Python.

---

### Q4: Explain the log1p transformation applied in the Forest Fires regression task.
**Answer**:
In the UCI Forest Fires dataset, the target variable `area` (burned hectares) is heavily zero-inflated (nearly 50% of recorded fires are small, quickly contained spot fires with 0 ha recorded) and exhibits severe positive skewness ($\text{skew} > 15$). Standard linear models with Gaussian error assumptions fail because large outliers dominate the loss function. The transformation $y = \ln(\text{area} + 1)$ stabilizes error variance, bounds small errors, and ensures strictly non-negative predictions when inverted via $\hat{\text{area}} = \exp(\hat{y}) - 1$.

---

### Q5: What is the difference between your Wildfire Screening Index and a real Wildfire Occurrence Model?
**Answer**:
The Covertype dataset does not contain meteorological variables (ambient temperature, wind speed, relative humidity, fuel moisture indices) or historical fire ignition timestamps. Therefore, it is impossible to calculate a true, calibrated probability of future fire occurrence. Our Wildfire Screening Index is explicitly an *exploratory terrain-hazard screening score*. It combines:
1. Proximity to historical fire points ($40\%$)
2. Slope gradient ($35\%$) — steeper slopes accelerate convective uphill heat pre-heating
3. Midday solar exposure ($25\%$) — midday hillshade indices dry out forest fuel beds
It serves as a relative terrain vulnerability index, not an ignition forecast.

---

### Q6: How does Random Forest handle the severe class imbalance in this dataset?
**Answer**:
The Covertype dataset has severe imbalance: Class 2 (Lodgepole Pine, 48.8%) and Class 1 (Spruce/Fir, 36.5%) represent over 85% of records, while Class 4 (Cottonwood/Willow, 0.47%) has only 2,747 rows.
Standard classifiers optimize overall accuracy by predicting only majority classes. To counteract this:
- We set `class_weight='balanced'`, which inversely weights sample losses proportional to class frequencies: $w_c = \frac{N}{C \cdot N_c}$.
- We report **Balanced Accuracy** and **Macro F1-score**, which weight all 7 classes equally, ensuring minority classes are accurately evaluated.

---

### Q7: Why is standardization mandatory prior to PCA and K-Means clustering?
**Answer**:
Both PCA and K-Means rely on Euclidean distances and covariance metrics:
- In our dataset, `Elevation` ranges from 1,859m to 3,858m ($\Delta = 2000$), while `Slope` ranges from 0° to 66° ($\Delta = 66$).
- Without standardization, the distance metric would be completely dominated by `Elevation`, treating a 1% change in elevation as vastly more significant than a 50% change in slope.
Standardization transforms each feature to mean $\mu = 0$ and standard deviation $\sigma = 1$, giving equal geometric weight to every environmental dimension.

---

### Q8: What does the K-Means Elbow curve and Silhouette score indicate?
**Answer**:
In K-Means clustering across $k \in [2, 10]$:
- The Elbow curve plots Within-Cluster Sum of Squares (inertia) vs $k$. As $k$ increases, inertia drops rapidly until $k=7$, where the rate of decrease diminishes.
- The Silhouette score measures how similar a point is to its own cluster compared to neighboring clusters: $s(i) \in [-1, 1]$.
- At $k=7$, natural clusters formed by K-Means align with the 7 ecological vegetation zones, showing that terrain factors alone drive the physical separation of tree communities.
