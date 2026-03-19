"""
Interactive matplotlib GUI for fault scarp offset measurement.

Replaces the MATLAB ginput / inputdlg workflow with a click-driven
matplotlib interface.  The user selects regions by clicking twice
(left edge, right edge) on the profile subplot.

Workflow mirrors Scarp_offset_v4g.m:
    1. Load & display profile
    2. (Optional) Subset profile
    3. (Optional) Exclude noisy sections (e.g., vegetation)
    4. Select lower far-field surface
    5. Select upper far-field surface
    6. Select scarp face
    7. Compute & display offset
    8. Repeat or save
"""

from __future__ import annotations

import sys
from pathlib import Path
from typing import Optional

import matplotlib
import matplotlib.pyplot as plt
import numpy as np
from matplotlib.widgets import Button, SpanSelector

from scarp_offset.core import (
    ScarpResult,
    compute_offset,
    fit_surface,
    slope_angle,
)
from scarp_offset.io import load_profile, save_results


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def _mask_range(h, e, xmin, xmax):
    """Return (h, e) with points inside [xmin, xmax] removed."""
    keep = ~((h >= xmin) & (h <= xmax))
    return h[keep], e[keep]


def _select_range(h, e, xmin, xmax):
    """Return (h, e) restricted to [xmin, xmax]."""
    mask = (h >= xmin) & (h <= xmax)
    return h[mask], e[mask]


# ---------------------------------------------------------------------------
# Main interactive session
# ---------------------------------------------------------------------------

class ScarpSession:
    """One interactive offset-measurement session for a single profile file.

    Usage::

        session = ScarpSession("profile.txt")
        session.run()          # opens the interactive figure
        session.results        # list[ScarpResult] after measurements
    """

    def __init__(self, filepath: str | Path):
        self.filepath = Path(filepath)
        self.profile_name = self.filepath.stem
        self.h_orig, self.e_orig = load_profile(self.filepath)
        self.h = self.h_orig.copy()
        self.e = self.e_orig.copy()
        self.results: list[ScarpResult] = []
        self._iteration = 0

        # Ensure profile faces left (increasing x is left-to-right)
        if self.h[0] > self.h[-1]:
            self.h = np.abs(self.h - self.h.max())
            self.h_orig = self.h.copy()

    # -----------------------------------------------------------------------
    # Public API
    # -----------------------------------------------------------------------

    def run(self):
        """Launch the interactive measurement loop."""
        print(f"\n  Profile: {self.profile_name}")
        print(f"  Points : {len(self.h)}")
        print(f"  X range: {self.h.min():.2f} – {self.h.max():.2f} m")
        print(f"  Y range: {self.e.min():.2f} – {self.e.max():.2f} m\n")

        measuring = True
        while measuring:
            self._iteration += 1
            # Reset to (possibly subsetted) data each iteration
            h_work = self.h.copy()
            e_work = self.e.copy()

            # Step 1: optional subset
            h_work, e_work = self._step_subset(h_work, e_work)

            # Step 2: optional exclude
            h_work, e_work = self._step_exclude(h_work, e_work)

            # Step 3-5: select surfaces and compute
            result = self._step_measure(h_work, e_work)

            if result is not None:
                self.results.append(result)
                self._print_result(result)

                pref = input("  Is this your preferred offset? [y/N]: ").strip().lower()
                if pref in ("y", "yes", "1"):
                    result.preferred = True

            again = input("\n  Re-run offset measurement? [Y/n]: ").strip().lower()
            if again in ("n", "no", "0"):
                measuring = False

        if self.results:
            self._save_prompt()

    # -----------------------------------------------------------------------
    # Interactive steps
    # -----------------------------------------------------------------------

    def _step_subset(self, h, e):
        """Optionally subset the profile."""
        ans = input("  Select a subset of the profile? [y/N]: ").strip().lower()
        if ans not in ("y", "yes", "1"):
            return h, e

        fig, axes = self._plot_profile(h, e, title="Click & drag to select subset")
        span_result = {}

        def on_select(xmin, xmax):
            span_result["xmin"] = xmin
            span_result["xmax"] = xmax

        span = SpanSelector(
            axes[1], on_select, "horizontal",
            useblit=True, props=dict(alpha=0.3, facecolor="tab:blue"),
            interactive=True, drag_from_anywhere=True,
        )
        print("    → Drag to select subset region, then close the window.")
        plt.show()

        if span_result:
            h, e = _select_range(h, e, span_result["xmin"], span_result["xmax"])
            print(f"    Subset to {len(h)} points "
                  f"({h.min():.1f} – {h.max():.1f} m).")
        return h, e

    def _step_exclude(self, h, e):
        """Optionally exclude noisy parts of the profile (e.g., vegetation)."""
        ans = input("  Exclude part of the profile? [y/N]: ").strip().lower()
        if ans not in ("y", "yes", "1"):
            return h, e

        excluding = True
        while excluding:
            fig, axes = self._plot_profile(h, e, title="Click & drag to select region to EXCLUDE")
            span_result = {}

            def on_select(xmin, xmax):
                span_result["xmin"] = xmin
                span_result["xmax"] = xmax

            span = SpanSelector(
                axes[1], on_select, "horizontal",
                useblit=True, props=dict(alpha=0.3, facecolor="tab:red"),
                interactive=True, drag_from_anywhere=True,
            )
            print("    → Drag to select region to exclude, then close the window.")
            plt.show()

            if span_result:
                h, e = _mask_range(h, e, span_result["xmin"], span_result["xmax"])
                print(f"    Excluded region. {len(h)} points remain.")

            more = input("    Exclude another region? [y/N]: ").strip().lower()
            if more not in ("y", "yes", "1"):
                excluding = False

        return h, e

    def _step_measure(self, h, e) -> Optional[ScarpResult]:
        """Select lower, upper, and scarp surfaces; compute offset."""
        dhor, sa = slope_angle(h, e)

        print("\n  Now select three regions on the profile plot:")
        print("    1) Lower far-field surface  (blue span)")
        print("    2) Upper far-field surface  (blue span)")
        print("    3) Scarp face               (red span)")
        print("  For each, drag a span, then close the window.\n")

        selections = {}
        for label, color in [
            ("lower far-field surface", "tab:blue"),
            ("upper far-field surface", "tab:blue"),
            ("scarp face", "tab:red"),
        ]:
            fig, axes = self._plot_profile(h, e, title=f"Select {label}")
            # Also show slope panel
            axes[0].plot(dhor, sa, "k:", alpha=0.4)
            axes[0].plot(dhor, sa, "b.", markersize=3)
            axes[0].set_ylabel("Slope (deg)")
            axes[0].grid(True)

            # Highlight already-selected regions
            for prev_label, (xmin, xmax) in selections.items():
                for ax in axes:
                    ax.axvspan(xmin, xmax, alpha=0.15, color="green", label=prev_label)

            span_result = {}

            def on_select(xmin, xmax, _sr=span_result):
                _sr["xmin"] = xmin
                _sr["xmax"] = xmax

            span = SpanSelector(
                axes[1], on_select, "horizontal",
                useblit=True,
                props=dict(alpha=0.3, facecolor=color),
                interactive=True, drag_from_anywhere=True,
            )
            plt.show()

            if not span_result:
                print(f"    No region selected for {label}. Aborting iteration.")
                return None

            selections[label] = (span_result["xmin"], span_result["xmax"])

        # Extract data for each segment
        lh, le = _select_range(h, e, *selections["lower far-field surface"])
        uh, ue = _select_range(h, e, *selections["upper far-field surface"])
        sh, se = _select_range(h, e, *selections["scarp face"])

        if len(lh) < 2 or len(uh) < 2 or len(sh) < 2:
            print("    Too few points in one or more selections. Aborting.")
            return None

        lower_fit = fit_surface(lh, le)
        upper_fit = fit_surface(uh, ue)
        scarp_fit = fit_surface(sh, se)

        x_bounds = (
            min(selections["lower far-field surface"][0],
                selections["upper far-field surface"][0]),
            max(selections["lower far-field surface"][1],
                selections["upper far-field surface"][1]),
        )

        try:
            result = compute_offset(lower_fit, upper_fit, scarp_fit, x_bounds)
        except ValueError as exc:
            print(f"    Calculation error: {exc}")
            return None

        result.version = self._iteration

        # Show result figure
        self._plot_result(h, e, dhor, sa, result, selections)

        include = input("  Include this result? [Y/n]: ").strip().lower()
        if include in ("n", "no", "0"):
            print("    Result discarded.")
            return None

        return result

    # -----------------------------------------------------------------------
    # Plotting helpers
    # -----------------------------------------------------------------------

    def _plot_profile(self, h, e, title=""):
        """Create the two-panel profile figure (slope + elevation)."""
        fig, axes = plt.subplots(2, 1, figsize=(12, 7), sharex=True)
        fig.canvas.manager.set_window_title(f"Scarp Offset — {self.profile_name}")

        dhor, sa = slope_angle(h, e)

        axes[0].plot(dhor, sa, "k:", alpha=0.4)
        axes[0].plot(dhor, sa, "b.", markersize=3)
        axes[0].set_ylabel("Slope (deg)")
        axes[0].grid(True, alpha=0.3)

        axes[1].plot(h, e, "k:", alpha=0.4)
        axes[1].plot(h, e, "r.", markersize=3)
        axes[1].set_xlabel("Horizontal distance (m)")
        axes[1].set_ylabel("Elevation (m)")
        axes[1].set_aspect("equal", adjustable="datalim")
        axes[1].grid(True, alpha=0.3)

        if title:
            fig.suptitle(title, fontsize=12, fontweight="bold")

        fig.tight_layout()
        return fig, axes

    def _plot_result(self, h, e, dhor, sa, result: ScarpResult, selections):
        """Show the final offset figure with regression lines and offset bar."""
        fig, axes = plt.subplots(2, 1, figsize=(13, 8), sharex=True)
        fig.canvas.manager.set_window_title(
            f"Offset result — {self.profile_name} v{result.version}"
        )

        # Slope panel
        axes[0].plot(dhor, sa, "k:", alpha=0.4)
        axes[0].plot(dhor, sa, "b.", markersize=3)
        axes[0].set_ylabel("Slope (deg)")
        axes[0].grid(True, alpha=0.3)

        # Profile panel
        axes[1].plot(h, e, "k:", alpha=0.4)
        axes[1].plot(h, e, "r.", markersize=3)

        lf = result.lower_fit
        uf = result.upper_fit
        sf = result.scarp_fit

        # Extend fitted lines toward the scarp
        ext = (uf.x.min() - lf.x.max()) / 2.0
        lx_ext = np.append(lf.x, lf.x[-1] + ext)
        ux_ext = np.insert(uf.x, 0, uf.x[0] - ext)

        axes[1].plot(lx_ext, lf.eval(lx_ext), "b-o", markersize=3, label="Lower surface")
        axes[1].plot(ux_ext, uf.eval(ux_ext), "b-o", markersize=3, label="Upper surface")
        axes[1].plot(sf.x, sf.eval(sf.x), "g-o", markersize=3, label="Scarp face")

        # Intersection points
        ix = [result.lower_intersection[0], result.upper_intersection[0]]
        iy = [result.lower_intersection[1], result.upper_intersection[1]]
        axes[1].plot(ix, iy, "go--", markersize=7)

        # Offset bar at inflection point
        ip = result.inflection_point
        y_lo = lf.eval(np.array([ip]))[0]
        y_hi = uf.eval(np.array([ip]))[0]
        axes[1].plot([ip, ip], [y_lo, y_hi], "r-", linewidth=2.5)
        axes[1].annotate(
            f"{result.scarp_offset:.2f} m",
            xy=(ip, (y_lo + y_hi) / 2),
            xytext=(15, 0), textcoords="offset points",
            fontsize=11, color="red", fontweight="bold",
            arrowprops=dict(arrowstyle="->", color="red"),
        )

        # Regression statistics text
        stats_text = (
            f"Lower: R²={lf.r_squared:.3f}, RMSE={lf.rmse:.3f} ({lf.n_points} pts, "
            f"slope={lf.slope_angle_deg:.2f}°)\n"
            f"Upper: R²={uf.r_squared:.3f}, RMSE={uf.rmse:.3f} ({uf.n_points} pts, "
            f"slope={uf.slope_angle_deg:.2f}°)\n"
            f"Scarp: slope={sf.slope_angle_deg:.2f}°"
        )
        axes[1].text(
            0.02, 0.02, stats_text, transform=axes[1].transAxes,
            fontsize=8, verticalalignment="bottom",
            bbox=dict(boxstyle="round,pad=0.4", facecolor="wheat", alpha=0.7),
        )

        axes[1].set_xlabel("Horizontal distance (m)")
        axes[1].set_ylabel("Elevation (m)")
        axes[1].set_aspect("equal", adjustable="datalim")
        axes[1].grid(True, alpha=0.3)
        axes[1].legend(loc="upper right", fontsize=8)

        fig.suptitle(
            f"Profile: {self.profile_name}  |  Version {result.version}  |  "
            f"Offset = {result.scarp_offset:.2f} m",
            fontsize=12, fontweight="bold",
        )
        fig.tight_layout()
        plt.show()

    # -----------------------------------------------------------------------
    # Output
    # -----------------------------------------------------------------------

    def _print_result(self, result: ScarpResult):
        """Print a single result summary to the terminal."""
        print(f"\n  ── Iteration {result.version} ──")
        print(f"  Scarp offset         : {result.scarp_offset:.2f} m")
        print(f"  Profile length       : {result.profile_length:.2f} m")
        print(f"  Lower surface slope  : {result.lower_fit.slope_angle_deg:.2f}°")
        print(f"  Upper surface slope  : {result.upper_fit.slope_angle_deg:.2f}°")
        print(f"  Scarp slope          : {result.scarp_fit.slope_angle_deg:.2f}°")
        print(f"  Inflection point     : {result.inflection_point:.2f} m")
        print()
        print(f"  Lower fit: R²={result.lower_fit.r_squared:.4f}  "
              f"RMSE={result.lower_fit.rmse:.4f}  "
              f"({result.lower_fit.n_points} points)")
        print(f"  Upper fit: R²={result.upper_fit.r_squared:.4f}  "
              f"RMSE={result.upper_fit.rmse:.4f}  "
              f"({result.upper_fit.n_points} points)")

    def _save_prompt(self):
        """Offer to save results."""
        ans = input("\n  Save results? [Y/n]: ").strip().lower()
        if ans in ("n", "no", "0"):
            print("  Results not saved.")
            return

        suffix = input("  Text to append to filename [e.g. your initials]: ").strip()
        if not suffix:
            suffix = "results"

        # Determine summary mode
        preferred = [r for r in self.results if r.preferred]
        offsets = [r.scarp_offset for r in self.results]

        if preferred:
            summary_offset = preferred[-1].scarp_offset
            summary_mode = "preferred"
        elif len(offsets) > 1:
            choice = input("  Summary method — (m)ean or mid(p)oint? [m/p]: ").strip().lower()
            if choice in ("p", "midpoint"):
                summary_offset = (min(offsets) + max(offsets)) / 2.0
                summary_mode = "midpoint"
            else:
                summary_offset = float(np.mean(offsets))
                summary_mode = "mean"
        else:
            summary_offset = offsets[0]
            summary_mode = "single"

        outdir = self.filepath.parent
        save_results(
            outdir=outdir,
            profile_name=self.profile_name,
            suffix=suffix,
            results=self.results,
            summary_offset=summary_offset,
            summary_mode=summary_mode,
        )
        print(f"\n  Files saved to {outdir}/")
