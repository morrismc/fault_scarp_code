"""
Core computational routines for fault scarp offset measurement.

Ported from Chris DuRoss' MATLAB code (Scarp_offset_v4g.m and slopeangle_f.m).
"""

from __future__ import annotations

import dataclasses
from dataclasses import dataclass, field
from typing import Optional

import numpy as np


# ---------------------------------------------------------------------------
# Slope-angle calculation (vectorised port of slopeangle_f.m)
# ---------------------------------------------------------------------------

def slope_angle(
    h: np.ndarray,
    e: np.ndarray,
) -> tuple[np.ndarray, np.ndarray]:
    """Compute local slope angles along a profile.

    Parameters
    ----------
    h : array-like
        Horizontal distance values.
    e : array-like
        Elevation values (same length as *h*).

    Returns
    -------
    dhor : ndarray
        Midpoint horizontal distances between successive points.
    sa : ndarray
        Slope angles in degrees at each midpoint.
    """
    h = np.asarray(h, dtype=float)
    e = np.asarray(e, dtype=float)
    dhor = (h[:-1] + h[1:]) / 2.0
    sa = np.degrees(np.arctan(np.diff(e) / np.diff(h)))
    return dhor, sa


# ---------------------------------------------------------------------------
# Surface fitting
# ---------------------------------------------------------------------------

@dataclass
class SurfaceFit:
    """Result of a linear regression on a surface segment."""

    slope: float          # polynomial coefficient (rise/run)
    intercept: float      # polynomial intercept
    slope_angle_deg: float
    r_squared: float
    rmse: float
    n_points: int
    x: np.ndarray         # horizontal values used
    y: np.ndarray         # elevation values used
    poly: np.ndarray      # [slope, intercept]

    def eval(self, x: np.ndarray) -> np.ndarray:
        """Evaluate the fitted line at given x positions."""
        return np.polyval(self.poly, x)


def fit_surface(h: np.ndarray, e: np.ndarray) -> SurfaceFit:
    """Fit a first-order polynomial (line) to a surface segment.

    Parameters
    ----------
    h, e : array-like
        Horizontal and elevation values for the segment.

    Returns
    -------
    SurfaceFit
    """
    h = np.asarray(h, dtype=float)
    e = np.asarray(e, dtype=float)

    poly = np.polyfit(h, e, 1)  # [slope, intercept]
    yfit = np.polyval(poly, h)

    ss_res = np.sum((e - yfit) ** 2)
    ss_tot = np.sum((e - np.mean(e)) ** 2)
    r_sq = 1.0 - ss_res / ss_tot if ss_tot > 0 else np.nan
    rmse = float(np.sqrt(np.mean((e - yfit) ** 2)))

    return SurfaceFit(
        slope=poly[0],
        intercept=poly[1],
        slope_angle_deg=float(np.degrees(np.arctan(poly[0]))),
        r_squared=float(r_sq),
        rmse=rmse,
        n_points=len(h),
        x=h,
        y=e,
        poly=poly,
    )


# ---------------------------------------------------------------------------
# Offset calculation
# ---------------------------------------------------------------------------

def _line_intersection(p1: np.ndarray, p2: np.ndarray) -> tuple[float, float]:
    """Return (x, y) where two lines y = p[0]*x + p[1] intersect."""
    if np.isclose(p1[0], p2[0]):
        raise ValueError("Lines are parallel — cannot compute intersection.")
    x = (p2[1] - p1[1]) / (p1[0] - p2[0])
    y = np.polyval(p1, x)
    return float(x), float(y)


@dataclass
class ScarpResult:
    """Complete result of a single scarp-offset measurement."""

    scarp_offset: float
    inflection_point: float
    lower_intersection: tuple[float, float]
    upper_intersection: tuple[float, float]
    lower_fit: SurfaceFit
    upper_fit: SurfaceFit
    scarp_fit: SurfaceFit
    profile_length: float
    preferred: bool = False
    version: Optional[int] = None


def compute_offset(
    lower_fit: SurfaceFit,
    upper_fit: SurfaceFit,
    scarp_fit: SurfaceFit,
    profile_x_bounds: tuple[float, float] | None = None,
) -> ScarpResult:
    """Compute vertical surface offset from three fitted surfaces.

    This reproduces the intersection-based method in Scarp_offset_v4g.m:

    1. Find where the scarp-slope line intersects the lower far-field line.
    2. Find where the scarp-slope line intersects the upper far-field line.
    3. The inflection point is the midpoint of those two x-values.
    4. The offset is the difference between the upper and lower far-field
       lines evaluated at the inflection point.

    Parameters
    ----------
    lower_fit, upper_fit, scarp_fit : SurfaceFit
        Fitted surfaces for the lower, upper, and scarp-face segments.
    profile_x_bounds : tuple, optional
        (x_lower_min, x_upper_max) used for profile length.  If *None*,
        derived from the surface fits.

    Returns
    -------
    ScarpResult
    """
    pl = lower_fit.poly
    pu = upper_fit.poly
    ps = scarp_fit.poly

    # Intersection of scarp line with lower surface
    int_xl, int_el = _line_intersection(pl, ps)
    # Intersection of scarp line with upper surface
    int_xu, int_eu = _line_intersection(pu, ps)

    inflection = (int_xl + int_xu) / 2.0
    offset = float(np.polyval(pu, inflection) - np.polyval(pl, inflection))

    if profile_x_bounds is not None:
        prof_len = profile_x_bounds[1] - profile_x_bounds[0]
    else:
        prof_len = float(
            max(upper_fit.x.max(), lower_fit.x.max())
            - min(upper_fit.x.min(), lower_fit.x.min())
        )

    return ScarpResult(
        scarp_offset=offset,
        inflection_point=inflection,
        lower_intersection=(int_xl, int_el),
        upper_intersection=(int_xu, int_eu),
        lower_fit=lower_fit,
        upper_fit=upper_fit,
        scarp_fit=scarp_fit,
        profile_length=prof_len,
    )
