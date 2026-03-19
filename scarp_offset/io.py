"""
File I/O for loading profiles and saving results.

Supports the same input formats as the original MATLAB code (.txt, .dat)
plus CSV files.
"""

from __future__ import annotations

import csv
import json
from pathlib import Path
from typing import TYPE_CHECKING

import numpy as np

if TYPE_CHECKING:
    from scarp_offset.core import ScarpResult


# ---------------------------------------------------------------------------
# Loading
# ---------------------------------------------------------------------------

def load_profile(filepath: str | Path) -> tuple[np.ndarray, np.ndarray]:
    """Load a two-column profile file (horizontal distance, elevation).

    Handles:
    - Whitespace- or tab-delimited text files (.txt, .dat)
    - Comma-separated files (.csv)
    - Lines starting with ``%`` or ``#`` are treated as comments.

    Returns
    -------
    h : ndarray
        Horizontal distance.
    e : ndarray
        Elevation.
    """
    filepath = Path(filepath)
    rows: list[tuple[float, float]] = []

    with open(filepath) as fh:
        for line in fh:
            line = line.strip()
            if not line or line.startswith("%") or line.startswith("#"):
                continue
            # Try comma, then whitespace
            parts = line.split(",") if "," in line else line.split()
            if len(parts) < 2:
                continue
            try:
                x, y = float(parts[0]), float(parts[1])
                rows.append((x, y))
            except ValueError:
                continue

    if not rows:
        raise ValueError(f"No valid data rows found in {filepath}")

    data = np.array(rows)
    return data[:, 0], data[:, 1]


# ---------------------------------------------------------------------------
# Saving
# ---------------------------------------------------------------------------

def save_results(
    outdir: Path,
    profile_name: str,
    suffix: str,
    results: list[ScarpResult],
    summary_offset: float,
    summary_mode: str,
) -> None:
    """Write summary and individual-measurement files.

    Produces files matching the original MATLAB output:

    - ``<name>_<suffix>-summary.csv``  — one-row summary
    - ``<name>_<suffix>-individual.csv`` — one row per iteration
    - ``<name>_<suffix>-results.json``  — machine-readable full dump
    """
    outdir = Path(outdir)
    base = f"{profile_name}_{suffix}"

    offsets = [r.scarp_offset for r in results]

    # ---- Summary CSV (mirrors MATLAB summary text file) ----
    summary_path = outdir / f"{base}-summary.csv"
    summary_data = {
        "summary_mode": summary_mode,
        "summary_offset_m": round(summary_offset, 4),
        "min_offset_m": round(min(offsets), 4),
        "max_offset_m": round(max(offsets), 4),
        "mean_profile_length_m": round(
            float(np.mean([r.profile_length for r in results])), 4
        ),
        "mean_lower_slope_deg": round(
            float(np.mean([r.lower_fit.slope_angle_deg for r in results])), 4
        ),
        "mean_upper_slope_deg": round(
            float(np.mean([r.upper_fit.slope_angle_deg for r in results])), 4
        ),
        "mean_scarp_slope_deg": round(
            float(np.mean([r.scarp_fit.slope_angle_deg for r in results])), 4
        ),
        "n_iterations": len(results),
    }
    with open(summary_path, "w", newline="") as f:
        writer = csv.DictWriter(f, fieldnames=list(summary_data.keys()))
        writer.writeheader()
        writer.writerow(summary_data)
    print(f"    Wrote {summary_path.name}")

    # ---- Individual CSV ----
    indiv_path = outdir / f"{base}-individual.csv"
    fields = [
        "version", "offset_m", "profile_length_m",
        "lower_slope_deg", "upper_slope_deg", "scarp_slope_deg",
        "lower_r2", "upper_r2", "lower_rmse", "upper_rmse",
        "lower_n_pts", "upper_n_pts", "preferred",
    ]
    with open(indiv_path, "w", newline="") as f:
        writer = csv.DictWriter(f, fieldnames=fields)
        writer.writeheader()
        for r in results:
            writer.writerow({
                "version": r.version,
                "offset_m": round(r.scarp_offset, 4),
                "profile_length_m": round(r.profile_length, 4),
                "lower_slope_deg": round(r.lower_fit.slope_angle_deg, 4),
                "upper_slope_deg": round(r.upper_fit.slope_angle_deg, 4),
                "scarp_slope_deg": round(r.scarp_fit.slope_angle_deg, 4),
                "lower_r2": round(r.lower_fit.r_squared, 6),
                "upper_r2": round(r.upper_fit.r_squared, 6),
                "lower_rmse": round(r.lower_fit.rmse, 6),
                "upper_rmse": round(r.upper_fit.rmse, 6),
                "lower_n_pts": r.lower_fit.n_points,
                "upper_n_pts": r.upper_fit.n_points,
                "preferred": int(r.preferred),
            })
    print(f"    Wrote {indiv_path.name}")

    # ---- JSON full dump ----
    json_path = outdir / f"{base}-results.json"
    json_data = {
        "profile_name": profile_name,
        "summary": summary_data,
        "iterations": [
            {
                "version": r.version,
                "scarp_offset_m": r.scarp_offset,
                "inflection_point_m": r.inflection_point,
                "profile_length_m": r.profile_length,
                "preferred": r.preferred,
                "lower_surface": {
                    "slope_deg": r.lower_fit.slope_angle_deg,
                    "r_squared": r.lower_fit.r_squared,
                    "rmse": r.lower_fit.rmse,
                    "n_points": r.lower_fit.n_points,
                },
                "upper_surface": {
                    "slope_deg": r.upper_fit.slope_angle_deg,
                    "r_squared": r.upper_fit.r_squared,
                    "rmse": r.upper_fit.rmse,
                    "n_points": r.upper_fit.n_points,
                },
                "scarp_face": {
                    "slope_deg": r.scarp_fit.slope_angle_deg,
                },
            }
            for r in results
        ],
    }
    with open(json_path, "w") as f:
        json.dump(json_data, f, indent=2)
    print(f"    Wrote {json_path.name}")
