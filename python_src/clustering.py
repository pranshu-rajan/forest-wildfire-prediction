"""
Clustering module: K-Means and Agglomerative clustering.

Covers Practical 8:
- Feature scaling (mandatory before clustering)
- Elbow method
- Silhouette score
- Cluster-size distributions
- Cluster profiles (mean feature values per cluster)
- Visualisation outputs
- Interpretation notes

Target labels are NEVER used as clustering inputs.
"""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any

import numpy as np
import pandas as pd
from sklearn.cluster import AgglomerativeClustering, KMeans
from sklearn.metrics import silhouette_score
from sklearn.preprocessing import StandardScaler

from python_src.logging_config import get_logger
from python_src.schemas import CONTINUOUS_FEATURES, TARGET_COLUMN

logger = get_logger(__name__)


def elbow_analysis(
    X: np.ndarray,
    k_range: range = range(2, 12),
    random_state: int = 42,
) -> tuple[list[int], list[float]]:
    """Run K-Means for each k in k_range. Return (k_values, inertias)."""
    k_values, inertias = [], []
    for k in k_range:
        km = KMeans(n_clusters=k, random_state=random_state, n_init=10)
        km.fit(X)
        k_values.append(k)
        inertias.append(float(km.inertia_))
        logger.info("K-Means k=%d: inertia=%.0f", k, km.inertia_)
    return k_values, inertias


def silhouette_analysis(
    X: np.ndarray,
    k_range: range = range(2, 12),
    random_state: int = 42,
    sample_n: int = 5_000,
) -> tuple[list[int], list[float]]:
    """Compute silhouette scores for each k. Samples X for speed."""
    rng = np.random.default_rng(random_state)
    if len(X) > sample_n:
        idx = rng.choice(len(X), size=sample_n, replace=False)
        X_s = X[idx]
    else:
        X_s = X

    k_values, scores = [], []
    for k in k_range:
        km = KMeans(n_clusters=k, random_state=random_state, n_init=10)
        labels = km.fit_predict(X_s)
        s = float(silhouette_score(X_s, labels, sample_size=min(2000, len(X_s))))
        k_values.append(k)
        scores.append(s)
        logger.info("Silhouette k=%d: %.4f", k, s)
    return k_values, scores


def fit_kmeans(
    X: np.ndarray,
    k: int,
    random_state: int = 42,
) -> KMeans:
    """Fit K-Means with chosen k."""
    km = KMeans(n_clusters=k, random_state=random_state, n_init=20)
    km.fit(X)
    logger.info("K-Means fitted (k=%d), inertia=%.0f.", k, km.inertia_)
    return km


def cluster_profile(
    X: np.ndarray,
    labels: np.ndarray,
    feature_names: list[str],
) -> pd.DataFrame:
    """Compute mean feature values per cluster."""
    df = pd.DataFrame(X, columns=feature_names)
    df["cluster"] = labels
    profile = df.groupby("cluster").mean().round(4)
    profile["cluster_size"] = df.groupby("cluster").size()
    return profile


def cluster_size_distribution(labels: np.ndarray) -> dict[int, int]:
    """Return {cluster_id: count} dict."""
    unique, counts = np.unique(labels, return_counts=True)
    return {int(k): int(v) for k, v in zip(unique, counts)}


def run_clustering_pipeline(
    df: pd.DataFrame,
    out_dir: Path,
    sample_n: int = 50_000,
    k_range: range = range(2, 11),
    best_k: int = 7,
    random_state: int = 42,
) -> dict[str, Any]:
    """Full clustering pipeline.

    Returns a results dict with elbow, silhouette, cluster profiles, etc.
    """
    cont_cols = [c for c in CONTINUOUS_FEATURES if c in df.columns]

    # Sample for speed
    rng = np.random.default_rng(random_state)
    if len(df) > sample_n:
        idx = rng.choice(len(df), size=sample_n, replace=False)
        work = df.iloc[idx].reset_index(drop=True)
        logger.info("Clustering on %d-row sample.", sample_n)
    else:
        work = df.copy()

    # Scale continuous features only (no target, no binary)
    X_raw = work[cont_cols].values
    scaler = StandardScaler()
    X_scaled = scaler.fit_transform(X_raw)

    # Elbow and silhouette
    k_vals, inertias = elbow_analysis(X_scaled, k_range=k_range, random_state=random_state)
    _, sil_scores = silhouette_analysis(X_scaled, k_range=k_range, random_state=random_state)

    # Best K-Means
    km = fit_kmeans(X_scaled, k=best_k, random_state=random_state)
    labels = km.labels_

    profile = cluster_profile(X_raw, labels, cont_cols)
    sizes = cluster_size_distribution(labels)
    sil_best = float(silhouette_score(
        X_scaled, labels, sample_size=min(5000, len(X_scaled))
    ))

    # Add ground-truth comparison (informational only — not clustering input)
    if TARGET_COLUMN in work.columns:
        work["cluster"] = labels
        ct_crosstab = pd.crosstab(work["cluster"], work[TARGET_COLUMN])
    else:
        ct_crosstab = None

    # Agglomerative clustering (alternative method)
    agg = AgglomerativeClustering(n_clusters=best_k, linkage="ward")
    agg_labels = agg.fit_predict(X_scaled[:min(5000, len(X_scaled))])
    agg_sil = float(silhouette_score(
        X_scaled[:min(5000, len(X_scaled))], agg_labels
    ))
    logger.info("Agglomerative clustering silhouette (k=%d): %.4f", best_k, agg_sil)

    results = {
        "k_range": list(k_range),
        "inertias": inertias,
        "silhouette_scores": sil_scores,
        "best_k": best_k,
        "best_k_silhouette": round(sil_best, 4),
        "agglomerative_silhouette": round(agg_sil, 4),
        "cluster_sizes": sizes,
        "cluster_profile": profile,
        "crosstab_vs_cover_type": ct_crosstab,
        "labels": labels,
        "feature_names": cont_cols,
        "scaler": scaler,
    }

    out_dir.mkdir(parents=True, exist_ok=True)

    # Save CSV outputs
    profile.to_csv(out_dir / "cluster_profiles.csv")
    pd.DataFrame({"k": k_vals, "inertia": inertias, "silhouette": sil_scores}).to_csv(
        out_dir / "cluster_elbow_silhouette.csv", index=False
    )
    work_out = work[cont_cols].copy()
    work_out["cluster"] = labels
    if TARGET_COLUMN in work.columns:
        work_out[TARGET_COLUMN] = work[TARGET_COLUMN].values
    work_out.to_csv(out_dir / "clustering_results.csv", index=False)

    if ct_crosstab is not None:
        ct_crosstab.to_csv(out_dir / "cluster_vs_cover_type.csv")

    return results
