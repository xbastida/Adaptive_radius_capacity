# 🔵 Adaptive Radius Capacity

> **A QGIS plugin** that dynamically expands a buffer around origin points until a configurable capacity threshold is met by the cumulative attribute values of surrounding target features.

---

## Overview

**Adaptive Radius Capacity** is a Python-based QGIS plugin (≥ 3.0) designed for spatial catchment analysis. Given a set of *origin* features (e.g. bike stations, schools, hospitals) and a set of *target* features (e.g. buildings, population centroids), the plugin grows a circular buffer around each origin — step by step — until the sum of a chosen attribute from the targets inside the buffer meets or exceeds the origin's capacity.

The result is a new polygon layer where each feature is the smallest circle that satisfies the capacity constraint, together with diagnostic fields indicating the achieved fill value and whether the constraint was actually saturated.

### Typical use cases

- 🚲 **Bike sharing** — Find the smallest catchment area per station that captures enough population demand to justify its dock capacity.
- 🏫 **School accessibility** — Determine how wide a radius each school needs to draw its target enrollment from surrounding buildings.
- 🏥 **Healthcare planning** — Compute service areas per hospital that cover a required number of inhabitants.
- 📦 **Logistics & supply chains** — Model adaptive delivery zones based on order volume targets.

---

## Features

| Feature | Details |
|---|---|
| **Adaptive buffer growth** | Iteratively expands the radius from a `step` increment up to a configurable `max_radius` |
| **Per-feature capacity** | Each origin can have its own capacity value read from a vector field |
| **Per-target filling weights** | Each target contributes a numeric weight (e.g. population) from a chosen field |
| **Fixed fallback values** | Global defaults used when no field is selected for capacity or filling |
| **Exact match mode** | Optionally pinpoints the precise inter-target distance at which capacity is saturated (slower but more accurate) |
| **Projected CRS support** | All distance computations are performed in a user-specified metric CRS (default: EPSG:25830) |
| **Bilingual UI** | The dialog supports English and Spanish interfaces |
| **Pure PyQGIS backend** | Uses `QgsSpatialIndex` for efficient candidate lookups — no external Python dependencies at runtime |

---

## Project Structure

```
Adaptive_radius_capacity/
├── adaptive_radius/            # QGIS plugin package
│   ├── __init__.py             # classFactory entry point
│   ├── adaptive_radius.py      # Plugin registration & GUI wiring
│   ├── adaptive_radius_dialog.py  # Qt dialog (bilingual EN/ES)
│   ├── core_logic.py           # Pure PyQGIS computation engine
│   ├── metadata.txt            # QGIS plugin metadata
│   └── icon.svg                # Toolbar icon
├── function_try.py             # Standalone testing / prototyping script
├── main.py                     # Development entry point
├── pyproject.toml              # Python project config (uv / pip)
└── README.md
```

---

## Requirements

- **QGIS** ≥ 3.0 (provides `qgis.core`, `qgis.PyQt`, `qgis.gui`)
- **Python** ≥ 3.12 (bundled with QGIS)

Development / standalone testing additionally requires:

```
geopandas >= 1.1.2
folium    >= 0.20.0
matplotlib >= 3.10.8
```

These are declared in `pyproject.toml` and can be installed via `uv` or `pip`.

---

## Installation

### Method 1 — QGIS Plugin Manager (recommended)

1. Open QGIS.
2. Go to **Plugins → Manage and Install Plugins… → Install from ZIP**.
3. Select the ZIP archive of this plugin.
4. Enable **Adaptive Radius Capacity** in the plugin list.

### Method 2 — Manual installation

Copy (or symlink) the `adaptive_radius/` folder to your QGIS plugins directory:

```bash
# Linux
~/.local/share/QGIS/QGIS3/profiles/default/python/plugins/

# macOS
~/Library/Application Support/QGIS/QGIS3/profiles/default/python/plugins/

# Windows
%APPDATA%\QGIS\QGIS3\profiles\default\python\plugins\
```

Then restart QGIS and enable the plugin via **Plugins → Manage and Install Plugins**.

---

## Usage

1. Load your **Origins** layer (points or polygons) and **Targets** layer (points or polygons) into QGIS.
2. Click the **Adaptive Radius** toolbar button, or go to **Plugins → Adaptive Radius → Compute Adaptive Radius…**.
3. Configure the dialog:

| Parameter | Description |
|---|---|
| **Origins Layer** | Features that act as the center of each buffer |
| **Capacity Field** | Numeric field from Origins representing the fill threshold per feature |
| **Fixed Capacity** | Fallback constant if no field is selected |
| **Targets Layer** | Features whose attribute values fill the buffer |
| **Filling Field** | Numeric field from Targets contributing to the cumulative fill |
| **Fixed Filling** | Fallback constant weight per target (default: 1.0) |
| **Step (m)** | Radius increment per iteration (default: 20 m) |
| **Max Radius (m)** | Hard upper bound on the buffer radius (default: 10 000 m) |
| **Projected CRS** | EPSG code for metric projection used in distance calculations (default: EPSG:25830) |
| **Exact Match** | When enabled, determines the precise radius at which the last necessary target enters the buffer |

4. Click **OK**. The result layer `Adaptive Radii (<step>m step)` will be added to your QGIS project automatically.

### Output layer fields

The output polygon layer inherits all fields of the Origins layer, plus three additional computed fields:

| Field | Type | Description |
|---|---|---|
| `adaptive_radius_m` | Double | Final buffer radius in metres |
| `covered_filling` | Double | Total filling value accumulated within the radius |
| `saturated` | Boolean | `True` if capacity was met; `False` if max radius was reached first |

---

## Algorithm

The core algorithm (implemented in `adaptive_radius/core_logic.py`) follows these steps:

```
For each origin feature:
  1. Project the origin centroid to the metric CRS.
  2. Start with radius = step_m.
  3. Query the spatial index for all target candidates within the bounding box.
  4. Filter candidates by exact circular distance ≤ radius.
  5. Sum the filling values of qualifying targets.
  6. If sum ≥ capacity  →  record radius & filling, mark as saturated. STOP.
  7. Otherwise  →  radius += step_m. If radius > max_radius, STOP.
  8. Buffer the origin centroid by the final radius and reproject back to the origin CRS.
```

In **Exact Match** mode, step 6 additionally sorts qualifying targets by distance and advances only to the distance of the last target needed to meet capacity.

---

## Development

### Running standalone tests

```bash
# Install dependencies with uv
uv sync

# Run the prototype script (no QGIS required)
python function_try.py
```

### Plugin reload during development

Use the [Plugin Reloader](https://plugins.qgis.org/plugins/plugin_reloader/) QGIS plugin to reload `adaptive_radius` without restarting QGIS.

---

## License

This project is open source. See [LICENSE](LICENSE) for details.

---

## Author

**xabi9**  
Contributions and issue reports are welcome.
