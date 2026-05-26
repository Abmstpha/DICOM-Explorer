"""Generate academic-style plots from loaded DICOM metadata (matplotlib → base64 PNG)."""
from __future__ import annotations

import base64
import io
from typing import Any, Dict, List, Optional

import matplotlib

matplotlib.use("Agg")
import matplotlib.pyplot as plt
import numpy as np
import pandas as pd


def _fig_to_b64(fig) -> str:
    buf = io.BytesIO()
    fig.savefig(buf, format="png", dpi=120, bbox_inches="tight", facecolor="white")
    plt.close(fig)
    buf.seek(0)
    return base64.b64encode(buf.read()).decode()


def _count_plot(
    counts: Dict[str, int],
    title: str,
    xlabel: str,
    color: str = "#1e4d6b",
    top_n: int = 12,
) -> Optional[str]:
    if not counts:
        return None
    items = sorted(counts.items(), key=lambda x: -x[1])[:top_n]
    labels = [k if k and k != "N/A" else "Not specified" for k, _ in items]
    values = [v for _, v in items]

    fig, ax = plt.subplots(figsize=(7, 4))
    y = np.arange(len(labels))
    ax.barh(y, values, color=color, alpha=0.88, edgecolor="white", linewidth=0.5)
    ax.set_yticks(y)
    ax.set_yticklabels(labels, fontsize=9)
    ax.invert_yaxis()
    ax.set_xlabel(xlabel, fontsize=10)
    ax.set_title(title, fontsize=11, fontweight="bold", pad=10)
    ax.spines["top"].set_visible(False)
    ax.spines["right"].set_visible(False)
    for i, v in enumerate(values):
        ax.text(v + 0.3, i, str(v), va="center", fontsize=8, color="#334155")
    fig.tight_layout()
    return _fig_to_b64(fig)


def generate_plot_bundle(records: List[dict]) -> Dict[str, Any]:
    if not records:
        return {"available": False, "message": "Load DICOM files first."}

    df = pd.DataFrame(records)
    plots: Dict[str, str] = {}

    mod = df["modality"].fillna("N/A").value_counts().to_dict()
    plots["modality_distribution"] = _count_plot(
        mod,
        "Figure 1 — Modality distribution (DICOM tag Modality)",
        "Number of instances",
        "#1e4d6b",
    )

    body = df["body_part"].fillna("N/A").value_counts().to_dict()
    plots["body_part_distribution"] = _count_plot(
        body,
        "Figure 2 — Body part examined (0018,0015)",
        "Count",
        "#2d6a4f",
    )

    sex = df["patient_sex"].fillna("N/A").value_counts().to_dict()
    plots["sex_distribution"] = _count_plot(
        sex,
        "Figure 3 — Patient sex (0010,0040)",
        "Count",
        "#5c4d7d",
    )

    ages = df["patient_age_years"].dropna()
    if not ages.empty:
        fig, ax = plt.subplots(figsize=(7, 4))
        ax.hist(ages, bins=min(12, max(3, int(ages.nunique()))), color="#b45309", edgecolor="white", alpha=0.9)
        ax.set_xlabel("Patient age (years, parsed from DICOM PatientAge)", fontsize=10)
        ax.set_ylabel("Frequency", fontsize=10)
        ax.set_title("Figure 4 — Patient age distribution", fontsize=11, fontweight="bold")
        ax.spines["top"].set_visible(False)
        ax.spines["right"].set_visible(False)
        fig.tight_layout()
        plots["age_histogram"] = _fig_to_b64(fig)

    bits = df["bits_allocated"].dropna().astype(int).value_counts().sort_index()
    if not bits.empty:
        fig, ax = plt.subplots(figsize=(6, 4))
        ax.bar(bits.index.astype(str), bits.values, color="#0369a1", edgecolor="white")
        ax.set_xlabel("Bits allocated per pixel", fontsize=10)
        ax.set_ylabel("Count", fontsize=10)
        ax.set_title("Figure 5 — Bits allocated (0028,0100)", fontsize=11, fontweight="bold")
        ax.spines["top"].set_visible(False)
        ax.spines["right"].set_visible(False)
        fig.tight_layout()
        plots["bits_allocated"] = _fig_to_b64(fig)

    # Modality × decodable pixel matrix
    if "has_pixel_data" in df.columns:
        cross = df.groupby("modality")["has_pixel_data"].agg(["sum", "count"])
        cross["no_pixel"] = cross["count"] - cross["sum"]
        fig, ax = plt.subplots(figsize=(8, 4))
        x = np.arange(len(cross))
        w = 0.35
        ax.bar(x - w / 2, cross["sum"], w, label="Pixel data decodable", color="#0d9488")
        ax.bar(x + w / 2, cross["no_pixel"], w, label="Header only / failed decode", color="#cbd5e1")
        ax.set_xticks(x)
        ax.set_xticklabels(cross.index, rotation=35, ha="right", fontsize=8)
        ax.set_ylabel("Files", fontsize=10)
        ax.set_title("Figure 6 — Pixel data availability by modality", fontsize=11, fontweight="bold")
        ax.legend(fontsize=8, frameon=False)
        ax.spines["top"].set_visible(False)
        ax.spines["right"].set_visible(False)
        fig.tight_layout()
        plots["pixel_by_modality"] = _fig_to_b64(fig)

    plots = {k: v for k, v in plots.items() if v}
    return {
        "available": True,
        "cohort_size": len(df),
        "plots": plots,
        "plot_labels": {
            "modality_distribution": "Modality distribution",
            "body_part_distribution": "Body part examined",
            "sex_distribution": "Patient sex",
            "age_histogram": "Patient age (years)",
            "bits_allocated": "Bits allocated",
            "pixel_by_modality": "Pixel data by modality",
        },
    }
