"""
Visualisation module: reusable plotting functions for EDA and model outputs.

All functions save figures to the configured figures directory and return
the figure object.  Matplotlib's non-interactive Agg backend is used for
headless execution.

Covers Units III and V: XY plots, bar charts, pie charts, boxplots,
heatmaps, small multiples, treemaps, multi-Y graphs, and more.
"""

from __future__ import annotations

import warnings
from pathlib import Path
from typing import Any

import matplotlib
matplotlib.use("Agg")  # headless backend — must be set before pyplot import
import matplotlib.pyplot as plt
import matplotlib.cm as cm
import numpy as np
import pandas as pd
import seaborn as sns

from python_src.logging_config import get_logger
from python_src.schemas import (
    CONTINUOUS_FEATURES,
    COVER_TYPE_NAMES,
    SOIL_FEATURES,
    TARGET_COLUMN,
    WILDERNESS_FEATURES,
)

logger = get_logger(__name__)

# Global style
sns.set_theme(style="whitegrid", palette="tab10", font_scale=1.1)
plt.rcParams.update({"figure.dpi": 120, "savefig.bbox": "tight"})

COVER_TYPE_COLORS = sns.color_palette("tab10", 7)
COVER_NAMES_LIST = [COVER_TYPE_NAMES[i] for i in range(1, 8)]


def _save(fig: plt.Figure, path: Path, tag: str = "") -> Path:
    path.parent.mkdir(parents=True, exist_ok=True)
    fig.savefig(path)
    plt.close(fig)
    logger.info("Figure saved: %s%s", path, f" ({tag})" if tag else "")
    return path


# ---------------------------------------------------------------------------
# Class distribution (bar + pie)
# ---------------------------------------------------------------------------

def plot_class_distribution(
    df: pd.DataFrame,
    out_dir: Path,
) -> list[Path]:
    """Bar chart and pie chart of Cover_Type class counts."""
    dist = df[TARGET_COLUMN].value_counts().sort_index()
    labels = [COVER_TYPE_NAMES.get(i, str(i)) for i in dist.index]
    counts = dist.values

    # Bar chart
    fig, ax = plt.subplots(figsize=(10, 5))
    bars = ax.bar(labels, counts, color=COVER_TYPE_COLORS)
    ax.set_title("Cover Type Class Distribution (Bar Chart)", fontsize=14, fontweight="bold")
    ax.set_xlabel("Cover Type")
    ax.set_ylabel("Count")
    ax.bar_label(bars, fmt="%d", padding=3, fontsize=9)
    plt.xticks(rotation=30, ha="right")
    saved_bar = _save(fig, out_dir / "class_distribution_bar.png", "bar chart")

    # Pie chart
    fig, ax = plt.subplots(figsize=(8, 8))
    wedges, texts, autotexts = ax.pie(
        counts,
        labels=labels,
        colors=COVER_TYPE_COLORS,
        autopct="%1.1f%%",
        startangle=140,
        pctdistance=0.82,
    )
    for at in autotexts:
        at.set_fontsize(8)
    ax.set_title("Cover Type Class Distribution (Pie Chart)", fontsize=14, fontweight="bold")
    saved_pie = _save(fig, out_dir / "class_distribution_pie.png", "pie chart")

    return [saved_bar, saved_pie]


# ---------------------------------------------------------------------------
# Missing value heatmap
# ---------------------------------------------------------------------------

def plot_missing_heatmap(
    df: pd.DataFrame,
    out_dir: Path,
    sample_n: int = 500,
    title: str = "Missing Value Heatmap",
    filename: str = "missing_value_heatmap.png",
) -> Path:
    """Heatmap of missing values across columns (sampled rows for readability)."""
    sample = df.sample(min(sample_n, len(df)), random_state=42)
    miss = sample.isnull()
    if not miss.any().any():
        # No missing values — create an informational plot
        fig, ax = plt.subplots(figsize=(8, 3))
        ax.text(0.5, 0.5, "No missing values detected", ha="center", va="center",
                fontsize=14, transform=ax.transAxes)
        ax.set_title(title)
        return _save(fig, out_dir / filename, "no-miss")

    fig, ax = plt.subplots(figsize=(12, 6))
    sns.heatmap(miss, yticklabels=False, cbar=False, cmap="viridis", ax=ax)
    ax.set_title(title, fontsize=14, fontweight="bold")
    ax.set_xlabel("Feature")
    return _save(fig, out_dir / filename, "missing heatmap")


# ---------------------------------------------------------------------------
# Continuous feature distributions
# ---------------------------------------------------------------------------

def plot_continuous_distributions(
    df: pd.DataFrame,
    out_dir: Path,
    sample_n: int = 50_000,
) -> Path:
    """Grid of histograms for all continuous features (small multiples)."""
    cont_cols = [c for c in CONTINUOUS_FEATURES if c in df.columns]
    work = df[cont_cols].sample(min(sample_n, len(df)), random_state=42)

    n = len(cont_cols)
    ncols = 5
    nrows = (n + ncols - 1) // ncols
    fig, axes = plt.subplots(nrows, ncols, figsize=(18, nrows * 3))
    axes = axes.flatten()

    for i, col in enumerate(cont_cols):
        axes[i].hist(work[col].dropna(), bins=50, color="steelblue", edgecolor="white", alpha=0.8)
        axes[i].set_title(col, fontsize=9)
        axes[i].set_xlabel("Value")
        axes[i].set_ylabel("Freq")

    for j in range(i + 1, len(axes)):
        axes[j].set_visible(False)

    fig.suptitle("Continuous Feature Distributions (Small Multiples)", fontsize=14, fontweight="bold")
    fig.tight_layout(rect=[0, 0, 1, 0.97])
    return _save(fig, out_dir / "continuous_distributions.png", "histograms")


# ---------------------------------------------------------------------------
# Box plots
# ---------------------------------------------------------------------------

def plot_boxplots(
    df: pd.DataFrame,
    out_dir: Path,
    sample_n: int = 50_000,
) -> Path:
    """Boxplots for continuous features grouped by Cover_Type."""
    cont_cols = [c for c in CONTINUOUS_FEATURES if c in df.columns]
    work = df[cont_cols + [TARGET_COLUMN]].sample(min(sample_n, len(df)), random_state=42)
    work["Cover_Name"] = work[TARGET_COLUMN].map(COVER_TYPE_NAMES)

    n = len(cont_cols)
    ncols = 2
    nrows = (n + 1) // 2
    fig, axes = plt.subplots(nrows, ncols, figsize=(16, nrows * 3.5))
    axes = axes.flatten()

    for i, col in enumerate(cont_cols):
        ax = axes[i]
        sns.boxplot(data=work, x="Cover_Name", y=col, ax=ax, palette="tab10",
                    order=[COVER_TYPE_NAMES[k] for k in range(1, 8) if COVER_TYPE_NAMES[k] in work["Cover_Name"].values])
        ax.set_title(col, fontsize=9)
        ax.set_xlabel("")
        ax.set_xticklabels(ax.get_xticklabels(), rotation=25, ha="right", fontsize=7)

    for j in range(i + 1, len(axes)):
        axes[j].set_visible(False)

    fig.suptitle("Continuous Features by Cover Type (Boxplots)", fontsize=14, fontweight="bold")
    fig.tight_layout(rect=[0, 0, 1, 0.97])
    return _save(fig, out_dir / "boxplots_by_cover_type.png", "boxplots")


# ---------------------------------------------------------------------------
# Correlation heatmap
# ---------------------------------------------------------------------------

def plot_correlation_heatmap(
    corr_matrix: pd.DataFrame,
    out_dir: Path,
) -> Path:
    """Heatmap of the Pearson correlation matrix for continuous features."""
    fig, ax = plt.subplots(figsize=(11, 9))
    mask = np.triu(np.ones_like(corr_matrix, dtype=bool))
    sns.heatmap(
        corr_matrix,
        mask=mask,
        annot=True,
        fmt=".2f",
        cmap="coolwarm",
        center=0,
        vmin=-1,
        vmax=1,
        linewidths=0.5,
        ax=ax,
    )
    ax.set_title("Pearson Correlation Matrix — Continuous Features", fontsize=14, fontweight="bold")
    return _save(fig, out_dir / "correlation_heatmap.png", "correlation")


# ---------------------------------------------------------------------------
# XY scatter plots
# ---------------------------------------------------------------------------

def plot_scatter_elevation_vs_distance(
    df: pd.DataFrame,
    out_dir: Path,
    sample_n: int = 10_000,
) -> Path:
    """XY scatter: Elevation vs Horizontal_Distance_To_Hydrology, coloured by Cover_Type."""
    work = df.sample(min(sample_n, len(df)), random_state=42)
    fig, ax = plt.subplots(figsize=(10, 7))
    for ct in range(1, 8):
        sub = work[work[TARGET_COLUMN] == ct]
        ax.scatter(
            sub["Elevation"],
            sub["Horizontal_Distance_To_Hydrology"],
            label=COVER_TYPE_NAMES[ct],
            alpha=0.4,
            s=8,
            color=COVER_TYPE_COLORS[ct - 1],
        )
    ax.set_xlabel("Elevation (m)")
    ax.set_ylabel("Horizontal Distance to Hydrology (m)")
    ax.set_title("Elevation vs Horizontal Distance to Hydrology by Cover Type", fontweight="bold")
    ax.legend(title="Cover Type", bbox_to_anchor=(1.02, 1), loc="upper left", fontsize=8)
    return _save(fig, out_dir / "scatter_elevation_vs_hydrology.png", "scatter XY")


# ---------------------------------------------------------------------------
# Wilderness area bar chart
# ---------------------------------------------------------------------------

def plot_wilderness_distribution(
    df: pd.DataFrame,
    out_dir: Path,
) -> Path:
    """Bar chart of observation counts per wilderness area."""
    wa_cols = [c for c in WILDERNESS_FEATURES if c in df.columns]
    wa_counts = {c: int(df[c].sum()) for c in wa_cols}
    wa_labels = {
        "Wilderness_Area1": "Rawah",
        "Wilderness_Area2": "Neota",
        "Wilderness_Area3": "Comanche Peak",
        "Wilderness_Area4": "Cache la Poudre",
    }
    fig, ax = plt.subplots(figsize=(9, 5))
    x = [wa_labels[k] for k in wa_cols]
    y = [wa_counts[k] for k in wa_cols]
    bars = ax.bar(x, y, color=sns.color_palette("Set2", len(wa_cols)))
    ax.bar_label(bars, fmt="%d", padding=3)
    ax.set_title("Observation Count by Wilderness Area", fontweight="bold")
    ax.set_xlabel("Wilderness Area")
    ax.set_ylabel("Count")
    return _save(fig, out_dir / "wilderness_area_distribution.png", "wilderness bar")


# ---------------------------------------------------------------------------
# Soil type frequency
# ---------------------------------------------------------------------------

def plot_soil_type_frequency(
    soil_df: pd.DataFrame,
    out_dir: Path,
) -> Path:
    """Horizontal bar chart of soil type activation frequencies."""
    fig, ax = plt.subplots(figsize=(10, 12))
    ax.barh(soil_df["soil_type"], soil_df["pct_active"], color="teal", alpha=0.8)
    ax.set_xlabel("% Rows Active")
    ax.set_title("Soil Type Activation Frequency (%)", fontweight="bold")
    ax.invert_yaxis()
    return _save(fig, out_dir / "soil_type_frequency.png", "soil freq")


# ---------------------------------------------------------------------------
# PCA explained variance
# ---------------------------------------------------------------------------

def plot_pca_explained_variance(
    explained_variance_ratio: np.ndarray,
    out_dir: Path,
) -> Path:
    """Scree plot and cumulative explained variance for PCA."""
    n = len(explained_variance_ratio)
    cumulative = np.cumsum(explained_variance_ratio)
    components = list(range(1, n + 1))

    fig, (ax1, ax2) = plt.subplots(1, 2, figsize=(14, 5))

    # Scree plot
    ax1.bar(components, explained_variance_ratio * 100, color="steelblue", alpha=0.8)
    ax1.set_xlabel("Principal Component")
    ax1.set_ylabel("Explained Variance (%)")
    ax1.set_title("PCA Scree Plot", fontweight="bold")

    # Cumulative variance
    ax2.plot(components, cumulative * 100, marker="o", color="darkorange", linewidth=2)
    ax2.axhline(90, color="red", linestyle="--", linewidth=1, label="90% threshold")
    ax2.axhline(95, color="purple", linestyle="--", linewidth=1, label="95% threshold")
    ax2.set_xlabel("Number of Components")
    ax2.set_ylabel("Cumulative Explained Variance (%)")
    ax2.set_title("Cumulative Explained Variance", fontweight="bold")
    ax2.legend()
    ax2.set_ylim(0, 101)

    fig.suptitle("PCA — Explained Variance Analysis", fontsize=14, fontweight="bold")
    fig.tight_layout()
    return _save(fig, out_dir / "pca_explained_variance.png", "PCA scree")


# ---------------------------------------------------------------------------
# Confusion matrix
# ---------------------------------------------------------------------------

def plot_confusion_matrix(
    cm: np.ndarray,
    class_names: list[str],
    model_name: str,
    out_dir: Path,
) -> Path:
    """Annotated heatmap confusion matrix."""
    fig, ax = plt.subplots(figsize=(9, 7))
    sns.heatmap(
        cm,
        annot=True,
        fmt="d",
        cmap="Blues",
        xticklabels=class_names,
        yticklabels=class_names,
        ax=ax,
    )
    ax.set_xlabel("Predicted Label")
    ax.set_ylabel("True Label")
    ax.set_title(f"Confusion Matrix — {model_name}", fontweight="bold")
    filename = f"confusion_matrix_{model_name.lower().replace(' ', '_')}.png"
    return _save(fig, out_dir / filename, "confusion matrix")


# ---------------------------------------------------------------------------
# Elbow / silhouette for clustering
# ---------------------------------------------------------------------------

def plot_elbow_curve(
    k_values: list[int],
    inertias: list[float],
    out_dir: Path,
) -> Path:
    """Elbow curve for K-Means cluster selection."""
    fig, ax = plt.subplots(figsize=(8, 5))
    ax.plot(k_values, inertias, marker="o", color="steelblue", linewidth=2)
    ax.set_xlabel("Number of Clusters (k)")
    ax.set_ylabel("Inertia (Within-cluster SSE)")
    ax.set_title("K-Means Elbow Curve", fontweight="bold")
    ax.set_xticks(k_values)
    return _save(fig, out_dir / "kmeans_elbow_curve.png", "elbow")


def plot_silhouette_scores(
    k_values: list[int],
    silhouette_scores: list[float],
    out_dir: Path,
) -> Path:
    """Silhouette scores vs number of clusters."""
    fig, ax = plt.subplots(figsize=(8, 5))
    ax.plot(k_values, silhouette_scores, marker="s", color="darkorange", linewidth=2)
    ax.set_xlabel("Number of Clusters (k)")
    ax.set_ylabel("Silhouette Score")
    ax.set_title("K-Means Silhouette Scores", fontweight="bold")
    ax.set_xticks(k_values)
    return _save(fig, out_dir / "kmeans_silhouette_scores.png", "silhouette")


# ---------------------------------------------------------------------------
# Model metric comparison (multi-Y bar chart)
# ---------------------------------------------------------------------------

def plot_model_comparison(
    metrics_df: pd.DataFrame,
    metric_cols: list[str],
    out_dir: Path,
) -> Path:
    """Multi-Y grouped bar chart comparing classifier performance metrics."""
    models = metrics_df["model"].tolist()
    x = np.arange(len(models))
    width = 0.8 / len(metric_cols)

    fig, ax = plt.subplots(figsize=(12, 6))
    for i, metric in enumerate(metric_cols):
        offset = (i - len(metric_cols) / 2 + 0.5) * width
        bars = ax.bar(x + offset, metrics_df[metric], width, label=metric.replace("_", " ").title())

    ax.set_xticks(x)
    ax.set_xticklabels(models, rotation=15, ha="right")
    ax.set_ylim(0, 1.0)
    ax.set_ylabel("Score")
    ax.set_title("Classifier Performance Comparison", fontweight="bold")
    ax.legend(loc="lower right")
    return _save(fig, out_dir / "model_comparison.png", "model comparison")


# ---------------------------------------------------------------------------
# Before/after imputation comparison
# ---------------------------------------------------------------------------

def plot_before_after_imputation(
    before_df: pd.DataFrame,
    after_df: pd.DataFrame,
    out_dir: Path,
    filename: str = "synthetic_cleaning_before_after.png",
) -> Path:
    """Side-by-side bar chart: missing value counts before and after imputation."""
    cols = before_df["column"].tolist()
    before_miss = before_df.set_index("column")["n_missing"]
    after_miss = after_df.set_index("column")["n_missing"]

    x = np.arange(len(cols))
    width = 0.35
    fig, ax = plt.subplots(figsize=(12, 5))
    ax.bar(x - width / 2, [before_miss.get(c, 0) for c in cols], width, label="Before Cleaning", color="tomato")
    ax.bar(x + width / 2, [after_miss.get(c, 0) for c in cols], width, label="After Cleaning", color="seagreen")
    ax.set_xticks(x)
    ax.set_xticklabels(cols, rotation=30, ha="right", fontsize=8)
    ax.set_ylabel("Missing Cell Count")
    ax.set_title("Missing Values Before vs After Median Imputation\n[Synthetic Demonstration Dataset]",
                 fontweight="bold")
    ax.legend()
    return _save(fig, out_dir / filename, "before/after imputation")


# ---------------------------------------------------------------------------
# Treemap (Unit V)
# ---------------------------------------------------------------------------

def plot_treemap_cover_type(
    df: pd.DataFrame,
    out_dir: Path,
) -> Path:
    """Treemap-style visualisation of cover type proportions using nested rectangles."""
    try:
        import matplotlib.patches as mpatches
        from matplotlib.patches import FancyBboxPatch

        dist = df[TARGET_COLUMN].value_counts().sort_values(ascending=False)
        total = dist.sum()
        labels = [f"{COVER_TYPE_NAMES.get(k, k)}\n{v:,}\n({v/total*100:.1f}%)" for k, v in dist.items()]
        sizes = dist.values

        fig, ax = plt.subplots(figsize=(14, 7))
        # Simple squarified treemap implementation
        x, y, w, h = 0.0, 0.0, 1.0, 1.0
        colors = COVER_TYPE_COLORS
        rects = _squarify(sizes, x, y, w, h)
        for i, (rx, ry, rw, rh) in enumerate(rects):
            color = colors[i % len(colors)]
            patch = plt.Rectangle((rx, ry), rw, rh, facecolor=color, edgecolor="white", linewidth=2)
            ax.add_patch(patch)
            if rw > 0.04 and rh > 0.04:
                ax.text(rx + rw / 2, ry + rh / 2, labels[i], ha="center", va="center",
                        fontsize=max(6, int(rw * 35)), wrap=True)

        ax.set_xlim(0, 1)
        ax.set_ylim(0, 1)
        ax.axis("off")
        ax.set_title("Treemap — Cover Type Distribution", fontsize=14, fontweight="bold")
        return _save(fig, out_dir / "treemap_cover_type.png", "treemap")
    except Exception as exc:
        logger.warning("Treemap generation failed (%s); skipping.", exc)
        return out_dir / "treemap_cover_type.png"


def _squarify(sizes, x, y, w, h):
    """Minimal squarified treemap layout. Returns list of (x, y, w, h) for each rect."""
    total = sum(sizes)
    if len(sizes) == 0:
        return []
    if len(sizes) == 1:
        return [(x, y, w, h)]

    rects = []
    remaining = list(sizes)
    rx, ry, rw, rh = x, y, w, h

    while len(remaining) > 1:
        if rw >= rh:
            # Split horizontally
            proportion = remaining[0] / sum(remaining)
            block_w = rw * proportion
            rects.append((rx, ry, block_w, rh))
            rx += block_w
            rw -= block_w
        else:
            proportion = remaining[0] / sum(remaining)
            block_h = rh * proportion
            rects.append((rx, ry, rw, block_h))
            ry += block_h
            rh -= block_h
        remaining.pop(0)
    rects.append((rx, ry, rw, rh))
    return rects


# ---------------------------------------------------------------------------
# Radial bar chart (Unit V)
# ---------------------------------------------------------------------------

def plot_radial_cover_distribution(
    df: pd.DataFrame,
    out_dir: Path,
) -> Path:
    """Radial/polar bar chart of cover type distribution (Unit V: Radial Tables)."""
    dist = df[TARGET_COLUMN].value_counts().sort_index()
    labels = [COVER_TYPE_NAMES.get(i, str(i)) for i in dist.index]
    values = dist.values
    n = len(values)

    angles = np.linspace(0, 2 * np.pi, n, endpoint=False)
    max_val = max(values)

    fig, ax = plt.subplots(figsize=(8, 8), subplot_kw={"projection": "polar"})
    bars = ax.bar(angles, values, width=2 * np.pi / n * 0.8, bottom=0.0,
                  color=COVER_TYPE_COLORS, alpha=0.85, edgecolor="white")
    ax.set_xticks(angles)
    ax.set_xticklabels(labels, fontsize=9)
    ax.set_title("Cover Type Distribution — Radial Chart", fontsize=13, fontweight="bold", pad=20)
    ax.yaxis.set_visible(False)
    return _save(fig, out_dir / "radial_cover_distribution.png", "radial chart")


# ---------------------------------------------------------------------------
# Regression scatter
# ---------------------------------------------------------------------------

def plot_regression_predictions(
    y_true: np.ndarray,
    y_pred: np.ndarray,
    model_name: str,
    out_dir: Path,
) -> Path:
    """Scatter plot of true vs predicted values for regression models."""
    fig, ax = plt.subplots(figsize=(7, 7))
    ax.scatter(y_true, y_pred, alpha=0.4, s=10, color="steelblue")
    lims = [min(y_true.min(), y_pred.min()) - 0.5, max(y_true.max(), y_pred.max()) + 0.5]
    ax.plot(lims, lims, "r--", linewidth=1.5, label="Perfect fit")
    ax.set_xlabel("True Burned Area (log-transformed)")
    ax.set_ylabel("Predicted")
    ax.set_title(f"True vs Predicted — {model_name}", fontweight="bold")
    ax.legend()
    filename = f"regression_true_vs_pred_{model_name.lower().replace(' ', '_')}.png"
    return _save(fig, out_dir / filename, "regression scatter")


# ---------------------------------------------------------------------------
# Feature importance
# ---------------------------------------------------------------------------

def plot_feature_importance(
    importances: np.ndarray,
    feature_names: list[str],
    model_name: str,
    out_dir: Path,
    top_n: int = 20,
) -> Path:
    """Horizontal bar chart of top-N feature importances."""
    idx = np.argsort(importances)[-top_n:]
    fig, ax = plt.subplots(figsize=(9, 6))
    ax.barh(
        [feature_names[i] for i in idx],
        importances[idx],
        color="steelblue",
        alpha=0.85,
    )
    ax.set_xlabel("Importance")
    ax.set_title(f"Top {top_n} Feature Importances — {model_name}", fontweight="bold")
    ax.invert_yaxis()
    filename = f"feature_importance_{model_name.lower().replace(' ', '_')}.png"
    return _save(fig, out_dir / filename, "feature importance")
