"""
scarp_offset — Fault scarp vertical offset measurement toolkit.

A Python port of Chris DuRoss' MATLAB Scarp_offset_v4g tool, used for
measuring vertical surface offsets across fault scarps from topographic
profiles.
"""

__version__ = "1.0.0"

from scarp_offset.core import (
    slope_angle,
    fit_surface,
    compute_offset,
    ScarpResult,
)
