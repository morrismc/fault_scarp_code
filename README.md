# scarp_offset — Fault Scarp Vertical Offset Measurement Tool

A Python toolkit for measuring **vertical surface offsets** across fault scarps
from topographic profiles.  Ported from Chris DuRoss'
[MATLAB code](https://www.usgs.gov/) (`Scarp_offset_v4g.m`) with improvements
for usability, efficiency, and reproducibility.

---

## What it does

Normal and reverse faults produce topographic scarps whose vertical offset
records cumulative or single-event displacement.  This tool lets you:

1. **Load** a topographic profile (horizontal distance vs. elevation).
2. **Interactively select** the lower far-field surface, upper far-field
   surface, and the scarp face on a matplotlib plot.
3. **Fit linear regressions** to each surface and compute:
   - Vertical surface offset at the scarp inflection point
   - Far-field and scarp-face slope angles
   - R² and RMSE goodness-of-fit statistics
4. **Iterate** — take multiple measurements on the same profile with
   different surface picks to quantify measurement uncertainty.
5. **Export** summary and per-iteration results as CSV and JSON files.

The interactive GUI uses matplotlib's `SpanSelector` widget — click and drag
to select regions instead of the MATLAB `ginput` point-clicking workflow.

---

## Quick start

### Requirements

- Python 3.9+
- numpy ≥ 1.22
- matplotlib ≥ 3.5

### Installation

```bash
# From this repository
pip install -e .

# Or just run directly (numpy and matplotlib must be installed)
python -m scarp_offset path/to/profile.txt
```

### Usage

```bash
# Single profile
scarp-offset my_profile.txt

# Or via python -m
python -m scarp_offset my_profile.txt

# Multiple profiles in sequence
scarp-offset profile1.txt --batch profile2.txt profile3.txt
```

### Programmatic use

```python
from scarp_offset import slope_angle, fit_surface, compute_offset
import numpy as np

# Load your own data
h = np.loadtxt("profile.txt", usecols=0)
e = np.loadtxt("profile.txt", usecols=1)

# Compute slope angles along the profile
dhor, sa = slope_angle(h, e)

# Fit surfaces to user-selected segments
lower_fit = fit_surface(h[0:50], e[0:50])
upper_fit = fit_surface(h[80:130], e[80:130])
scarp_fit = fit_surface(h[50:80], e[50:80])

# Compute offset
result = compute_offset(lower_fit, upper_fit, scarp_fit)
print(f"Vertical offset: {result.scarp_offset:.2f} m")
print(f"Inflection point: {result.inflection_point:.2f} m")
```

---

## Input file format

Two-column text files with horizontal distance and elevation in the same
units (typically meters).  Comment lines starting with `%` or `#` are
ignored.  Supported formats: `.txt`, `.dat`, `.csv`.

```
# Profile X, measured at site Y
# Horizontal distance (m)    Elevation (m)
0.00    2087.79
0.99    2087.79
1.99    2087.78
3.00    2087.77
...
```

---

## Interactive workflow

The measurement workflow follows the same logic as the original MATLAB tool:

| Step | Action |
|------|--------|
| 1 | Load profile and display slope + elevation subplots |
| 2 | *Optional:* Subset the profile to zoom into the scarp region |
| 3 | *Optional:* Exclude noisy data (vegetation, structures, etc.) |
| 4 | **Select lower far-field surface** by dragging a horizontal span |
| 5 | **Select upper far-field surface** by dragging a horizontal span |
| 6 | **Select scarp face** by dragging a horizontal span |
| 7 | Review computed offset and regression statistics |
| 8 | Accept or discard the measurement |
| 9 | Mark as preferred offset (optional) |
| 10 | Repeat for additional iterations, or save results |

### Tips for surface selection

- Use the **slope-angle subplot** (upper panel) to identify where the
  far-field surfaces are flat and where the scarp face is steepest.
- Pick far-field surfaces **away from the scarp** to avoid including the
  scarp-to-surface transition in the regression.
- Run **3–5 iterations** with slightly different picks to build a
  min/max/preferred offset range.

---

## Output files

After completing measurements, three files are written:

| File | Contents |
|------|----------|
| `<name>_<suffix>-summary.csv` | Summary offset (preferred/mean/midpoint), min, max, mean slopes, iteration count |
| `<name>_<suffix>-individual.csv` | Per-iteration: offset, slopes, R², RMSE, point counts, preferred flag |
| `<name>_<suffix>-results.json` | Machine-readable full results for downstream analysis |

---

## How offset is calculated

The method follows the classic three-line intersection approach used in
paleoseismology (e.g., [Bucknam & Anderson, 1979](https://doi.org/10.1130/0016-7606(1979)90<1303:EOLFSF>2.0.CO;2)):

1. **Linear regression** is fit to the lower far-field surface, upper
   far-field surface, and scarp face independently.
2. The **intersections** between the scarp-face line and each far-field
   line are computed.
3. The **inflection point** is the horizontal midpoint between those two
   intersections.
4. The **vertical offset** is the difference between the upper and lower
   far-field lines evaluated at the inflection point.

This measures the **vertical surface offset** (also called vertical
separation), not the dip-slip displacement, which requires knowledge of
the fault dip angle.

---

## Improvements over the MATLAB version

| MATLAB (v4g) | Python |
|---|---|
| Point-clicking with `ginput` (two clicks per selection) | Drag-to-select `SpanSelector` — faster and more intuitive |
| `inputdlg` modal dialogs | Simple terminal prompts |
| `eval()` for file I/O (security/maintenance risk) | Direct `numpy` / standard library I/O |
| `str2num` (deprecated) | Proper type handling |
| Bitwise `&` in scalar `if` statements | Correct boolean logic |
| Bug: prints `lower_RMSE` for upper surface (line 595) | Fixed |
| R² computed via `(n-1)*var` (correct but indirect) | Explicit SS_res / SS_tot |
| Loop-based midpoint calculation in `slopeangle_f` | Fully vectorized with numpy |
| Output as MATLAB `.mat` / plain text | CSV + JSON for interoperability |
| Results plotted but not annotated | On-figure statistics box and labeled offset bar |
| No `--help` or usage info | `argparse` CLI with built-in help |
| Requires MATLAB license | Free and open-source (numpy + matplotlib) |

---

## Related tools and literature

If you work with fault scarp topographic data, these tools may also be
useful:

### Python tools

- **[MCSST](https://esurf.copernicus.org/articles/8/211/2020/)** — Monte
  Carlo Slip Statistics Toolkit.  Jupyter-based GUI for bulk dip-slip
  estimation with uncertainty quantification.  Good for processing many
  profiles across a fault.

- **[scarplet](https://github.com/stgl/scarplet)** — Template-matching on
  DEMs for detecting and dating fault scarps using diffusion models.
  Useful for regional-scale scarp identification and relative dating.

### MATLAB tools

- **[3D_Fault_Offsets](https://agupubs.onlinelibrary.wiley.com/doi/full/10.1002/2017jb014863)**
  (Stewart et al., 2018) — Automated lateral and vertical offset
  measurement from point clouds along faults.

- **[Auto_Throw](https://www.sciencedirect.com/science/article/pii/S0191814125000574)**
  (2025) — Piecewise linear fitting to automate throw measurements on
  normal fault scarps with uncertainty from many configurations.

### Key references

- Bucknam, R.C. & Anderson, R.E. (1979). Estimation of fault-scarp ages
  from a scarp-height–slope-angle relationship. *Geology*, 7, 11–14.
- DuRoss, C.B. et al. (2019). Holocene and latest Pleistocene
  paleoseismology of the Borah Peak fault.  *USGS*.
- Wells, D.L. & Coppersmith, K.J. (1994). New empirical relationships
  among magnitude, rupture length, rupture width, rupture area, and
  surface displacement.  *BSSA*, 84(4), 974–1002.

---

## Project structure

```
fault_scarp_code/
├── scarp_offset/            # Python package
│   ├── __init__.py          # Public API
│   ├── __main__.py          # CLI entry point
│   ├── core.py              # slope_angle, fit_surface, compute_offset
│   ├── interactive.py       # Matplotlib interactive GUI session
│   └── io.py                # Profile loading and result saving
├── Scarp_offset_v4g.m       # Original MATLAB script (reference)
├── slopeangle_f.m           # Original MATLAB function (reference)
├── Instructions for Scarp_Offset_v4g.docx
├── pyproject.toml           # Package configuration
├── LICENSE
└── README.md
```

---

## License

MIT — see [LICENSE](LICENSE).

## Credits

Original MATLAB code by **Chris DuRoss** (USGS), `cduross@usgs.gov`,
version v4g (December 6, 2016).  Python port maintains the same
scientific methodology while modernizing the interface and code quality.
