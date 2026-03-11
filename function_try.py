"""
Adaptive Radius Calculator
===========================
For each origin point, incrementally expand a buffer (Euclidean) until the sum
of covered target-point "filling" values meets or exceeds the origin's
"capacity".  Returns a GeoDataFrame with the computed radius, total covered
filling, and a saturation flag.
"""

from pathlib import Path
from typing import Union

import geopandas as gpd
import numpy as np
import pandas as pd
from shapely.geometry import Point

# ---------------------------------------------------------------------------
# Core function
# ---------------------------------------------------------------------------

def compute_adaptive_radius(
    origins: Union[gpd.GeoDataFrame, str, Path],
    targets: Union[gpd.GeoDataFrame, str, Path],
    capacity_col: str,
    filling_col: str,
    step_m: float = 20.0,
    max_radius_m: float = 10_000.0,
    projected_crs: str = "EPSG:25830",
) -> gpd.GeoDataFrame:
    """Compute an adaptive radius for every origin point.

    Parameters
    ----------
    origins : GeoDataFrame | str | Path
        Origin features.  Must contain *capacity_col* and a geometry column.
    targets : GeoDataFrame | str | Path
        Target features.  Must contain *filling_col* and a geometry column.
    capacity_col : str
        Column in *origins* that holds the capacity value for each origin.
    filling_col : str
        Column in *targets* that holds the filling value for each target.
    step_m : float, default 100
        Buffer-expansion step in **metres**.
    max_radius_m : float, default 10_000
        Safety cap – stop expanding even if capacity is not yet met.
    projected_crs : str, default "EPSG:25830"
        A projected CRS with metre units used for distance computation.

    Returns
    -------
    GeoDataFrame
        Copy of *origins* (in its original CRS) with extra columns:
        ``adaptive_radius_m``, ``covered_filling``, ``saturated``, and
        ``buffer_geometry`` (the final buffer polygon, also in original CRS).
    """

    # ---- 1. Load if paths ------------------------------------------------
    if not isinstance(origins, gpd.GeoDataFrame):
        origins = gpd.read_file(origins)
    if not isinstance(targets, gpd.GeoDataFrame):
        targets = gpd.read_file(targets)

    # ---- 2. Validate columns ---------------------------------------------
    if capacity_col not in origins.columns:
        raise ValueError(
            f"capacity_col '{capacity_col}' not found in origins. "
            f"Available: {list(origins.columns)}"
        )
    if filling_col not in targets.columns:
        raise ValueError(
            f"filling_col '{filling_col}' not found in targets. "
            f"Available: {list(targets.columns)}"
        )

    original_crs = origins.crs

    # ---- 3. Reproject to metric CRS --------------------------------------
    origins_proj = origins.to_crs(projected_crs)
    targets_proj = targets.to_crs(projected_crs)

    # ---- 4. Compute centroids for non-Point geometries -------------------
    origin_centroids = origins_proj.geometry.apply(
        lambda g: g.centroid if g.geom_type != "Point" else g
    )
    target_centroids = targets_proj.geometry.apply(
        lambda g: g.centroid if g.geom_type != "Point" else g
    )

    # Build arrays for fast access
    target_x = np.array([p.x for p in target_centroids])
    target_y = np.array([p.y for p in target_centroids])
    target_filling = targets[filling_col].values.astype(float)

    # ---- 5. Spatial index on target centroids ----------------------------
    target_centroids_gs = gpd.GeoSeries(target_centroids, crs=projected_crs)
    sindex = target_centroids_gs.sindex

    # ---- 6. Iterate over each origin ------------------------------------
    radii = []
    covered_fillings = []
    saturated_flags = []
    buffer_geoms = []

    for idx, origin_pt in enumerate(origin_centroids):
        capacity = float(origins[capacity_col].iloc[idx])
        ox, oy = origin_pt.x, origin_pt.y

        radius = step_m
        final_filling = 0.0
        found = False

        while radius <= max_radius_m:
            # Bounding-box pre-filter via spatial index
            minx, miny = ox - radius, oy - radius
            maxx, maxy = ox + radius, oy + radius
            candidate_idxs = list(sindex.intersection((minx, miny, maxx, maxy)))

            if candidate_idxs:
                # Precise Euclidean filter
                dx = target_x[candidate_idxs] - ox
                dy = target_y[candidate_idxs] - oy
                dists = np.sqrt(dx * dx + dy * dy)
                within_mask = dists <= radius
                filling_sum = float(target_filling[candidate_idxs][within_mask].sum())
            else:
                filling_sum = 0.0

            if filling_sum >= capacity:
                final_filling = filling_sum
                found = True
                break

            radius += step_m

        if not found:
            # Reached max radius without meeting capacity
            final_filling = filling_sum
            radius = min(radius, max_radius_m)

        radii.append(radius)
        covered_fillings.append(final_filling)
        saturated_flags.append(found)
        buffer_geoms.append(origin_pt.buffer(radius))

    # ---- 7. Build result GeoDataFrame ------------------------------------
    result = origins.copy()
    result["adaptive_radius_m"] = radii
    result["covered_filling"] = covered_fillings
    result["saturated"] = saturated_flags

    # Convert buffer polygons back to original CRS
    buffer_gs = gpd.GeoSeries(buffer_geoms, crs=projected_crs).to_crs(original_crs)
    result["buffer_geometry"] = buffer_gs.values

    return result


# ---------------------------------------------------------------------------
# Demo / CLI entry point
# ---------------------------------------------------------------------------

if __name__ == "__main__":
    project_dir = Path(__file__).parent

    # Load data
    stations = gpd.read_file(project_dir / "stations_with_h3_nuevo_acometida.gpkg")
    buildings = gpd.read_file(project_dir / "buildings_with_population.gpkg")
    buildings["Total_building"] = buildings["Total_building"] / 50

    print(f"Stations:  {len(stations)} features, CRS={stations.crs}")
    print(f"Buildings: {len(buildings)} features, CRS={buildings.crs}")
    print()

    result = compute_adaptive_radius(
        origins=stations,
        targets=buildings,
        capacity_col="Total de anclajes",
        filling_col="Total_building",
        step_m=50,
    )

    # Pretty-print summary
    print(result[
        ["Nombre", "Total de anclajes", "adaptive_radius_m",
         "covered_filling", "saturated"]
    ].to_string(index=False))

    # Save output
    out_path = project_dir / "stations_adaptive_radius.gpkg"
    result.drop(columns=["buffer_geometry"]).to_file(out_path, driver="GPKG")
    print(f"\nResults saved to {out_path}")

    # ---- Folium map -------------------------------------------------------
    import folium
    from branca.colormap import LinearColormap
    import webbrowser

    # Colour ramp based on radius
    radii = result["adaptive_radius_m"]
    cmap = LinearColormap(
        ["#2ecc71", "#f1c40f", "#e67e22", "#e74c3c"],
        vmin=radii.min(), vmax=radii.max(),
        caption="Adaptive radius (m)",
    )

    centre_lat = result.geometry.y.mean()
    centre_lon = result.geometry.x.mean()
    m = folium.Map(location=[centre_lat, centre_lon], zoom_start=14,
                   tiles="CartoDB dark_matter")

    # Buffer polygons
    buf_group = folium.FeatureGroup(name="Buffers")
    for _, row in result.iterrows():
        buf_geo = row["buffer_geometry"]
        coords = [(lat, lon) for lon, lat in buf_geo.exterior.coords]
        colour = cmap(row["adaptive_radius_m"])
        sat_label = "✅ Saturated" if row["saturated"] else "❌ Unsaturated"
        popup_html = (
            f"<b>{row['Nombre']}</b><br>"
            f"Capacity: {row['Total de anclajes']}<br>"
            f"Radius: {row['adaptive_radius_m']:.0f} m<br>"
            f"Covered filling: {row['covered_filling']:.1f}<br>"
            f"{sat_label}"
        )
        folium.Polygon(
            locations=coords,
            color=colour, weight=2,
            fill=True, fill_color=colour, fill_opacity=0.15,
            popup=folium.Popup(popup_html, max_width=260),
        ).add_to(buf_group)
    buf_group.add_to(m)

    # Origin markers
    origin_group = folium.FeatureGroup(name="Stations")
    for _, row in result.iterrows():
        colour = cmap(row["adaptive_radius_m"])
        sat_label = "✅ Saturated" if row["saturated"] else "❌ Unsaturated"
        popup_html = (
            f"<b>{row['Nombre']}</b><br>"
            f"Capacity: {row['Total de anclajes']}<br>"
            f"Radius: {row['adaptive_radius_m']:.0f} m<br>"
            f"Covered filling: {row['covered_filling']:.1f}<br>"
            f"{sat_label}"
        )
        folium.CircleMarker(
            location=[row.geometry.y, row.geometry.x],
            radius=6, color="white", weight=1.5,
            fill=True, fill_color=colour, fill_opacity=1.0,
            popup=folium.Popup(popup_html, max_width=260),
            tooltip=row["Nombre"],
        ).add_to(origin_group)
    origin_group.add_to(m)

    # Target markers (buildings)
    target_group = folium.FeatureGroup(name="Buildings", show=False)
    for _, trow in buildings.iterrows():
        centroid = trow.geometry.centroid
        folium.CircleMarker(
            location=[centroid.y, centroid.x],
            radius=2, color="#f1c40f", weight=0.5,
            fill=True, fill_color="#f1c40f", fill_opacity=0.6,
            tooltip=f"Filling: {trow['Total_building']:.1f}",
        ).add_to(target_group)
    target_group.add_to(m)

    cmap.add_to(m)
    folium.LayerControl(collapsed=False).add_to(m)

    map_path = project_dir / "adaptive_radius_map.html"
    m.save(str(map_path))
    print(f"Map saved to {map_path}")
    webbrowser.open(f"file://{map_path}")