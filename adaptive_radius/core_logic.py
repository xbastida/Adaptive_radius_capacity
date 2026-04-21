from qgis.core import (
    QgsVectorLayer,
    QgsFeature,
    QgsGeometry,
    QgsSpatialIndex,
    QgsCoordinateReferenceSystem,
    QgsCoordinateTransform,
    QgsProject,
    QgsField,
    QgsFields,
    QgsWkbTypes,
    QgsRectangle
)
from qgis.PyQt.QtCore import QVariant
import math

def compute_adaptive_radius(
    origin_layer: QgsVectorLayer,
    target_layer: QgsVectorLayer,
    capacity_col: str,
    capacity_default: float,
    filling_col: str,
    filling_default: float,
    step_m: float = 20.0,
    max_radius_m: float = 10_000.0,
    projected_crs_str: str = "EPSG:25830",
    exact_match: bool = False
) -> QgsVectorLayer:
    """Compute an adaptive radius for every origin point using pure PyQGIS API."""
    
    # 1. Coordinate Transforms
    proj_crs = QgsCoordinateReferenceSystem(projected_crs_str)
    
    transform_context = QgsProject.instance().transformContext()
    orig_to_proj = QgsCoordinateTransform(origin_layer.crs(), proj_crs, transform_context)
    targ_to_proj = QgsCoordinateTransform(target_layer.crs(), proj_crs, transform_context)
    proj_to_orig = QgsCoordinateTransform(proj_crs, origin_layer.crs(), transform_context)

    # 2. Extract targets
    target_idx = target_layer.fields().lookupField(filling_col) if filling_col else -1
        
    target_sindex = QgsSpatialIndex()
    target_data = {} # fid -> (x, y, filling)
    
    for f in target_layer.getFeatures():
        geom = f.geometry()
        if geom.isNull():
            continue
            
        geom.transform(targ_to_proj)
        
        # Get centroid
        if geom.type() != QgsWkbTypes.PointGeometry:
            centroid_geom = geom.centroid()
        else:
            centroid_geom = geom
            
        pt = centroid_geom.asPoint()
        
        # Insert into spatial index
        new_f = QgsFeature(f.id())
        new_f.setGeometry(centroid_geom)
        target_sindex.insertFeature(new_f)
        
        if target_idx != -1:
            try:
                fill_val = float(f.attributes()[target_idx])
            except (ValueError, TypeError):
                fill_val = 0.0
        else:
            fill_val = filling_default
            
        target_data[f.id()] = (pt.x(), pt.y(), fill_val)

    # 3. Prepare resulting memory layer.
    res_layer = QgsVectorLayer(
        f"Polygon?crs={origin_layer.crs().authid()}", 
        "Adaptive Radius Result", 
        "memory"
    )
    res_pr = res_layer.dataProvider()
    
    fields = origin_layer.fields()
    fields.append(QgsField("adaptive_radius_m", QVariant.Double))
    fields.append(QgsField("covered_filling", QVariant.Double))
    fields.append(QgsField("saturated", QVariant.Bool))
    
    res_pr.addAttributes(fields.toList())
    res_layer.updateFields()
    
    cap_idx = origin_layer.fields().lookupField(capacity_col) if capacity_col else -1

    out_features = []
    
    # 4. Process origins
    for f in origin_layer.getFeatures():
        geom = f.geometry()
        if geom.isNull():
            continue
            
        geom.transform(orig_to_proj)
        
        if geom.type() != QgsWkbTypes.PointGeometry:
            centroid_geom = geom.centroid()
        else:
            centroid_geom = geom
            
        pt = centroid_geom.asPoint()
        ox, oy = pt.x(), pt.y()
        
        if cap_idx != -1:
            try:
                capacity = float(f.attributes()[cap_idx])
            except (ValueError, TypeError):
                capacity = 0.0
        else:
            capacity = capacity_default
            
        radius = step_m
        final_filling = 0.0
        found = False
        
        while radius <= max_radius_m:
            # Query spatial index
            minx, miny = ox - radius, oy - radius
            maxx, maxy = ox + radius, oy + radius
            
            rect = QgsRectangle(minx, miny, maxx, maxy)
            candidate_ids = target_sindex.intersects(rect)
            
            filling_sum = 0.0
            targets_in_radius = []
            for cid in candidate_ids:
                tx, ty, t_fill = target_data[cid]
                dist = math.sqrt((tx - ox)**2 + (ty - oy)**2)
                if dist <= radius:
                    filling_sum += t_fill
                    if exact_match:
                        targets_in_radius.append((dist, t_fill))
                    
            if filling_sum >= capacity:
                if exact_match:
                    targets_in_radius.sort(key=lambda t: t[0])
                    acc_fill = 0.0
                    exact_rad = radius
                    for d, t_fill_val in targets_in_radius:
                        acc_fill += t_fill_val
                        exact_rad = d
                        if acc_fill >= capacity:
                            break
                    final_filling = acc_fill
                    radius = exact_rad
                else:
                    final_filling = filling_sum
                found = True
                break
                
            radius += step_m
            
        if not found:
            # Reached max radius without meeting capacity
            final_filling = filling_sum
            radius = min(radius, max_radius_m)
            
        # Create output geometry: a buffer around the origin centroid in the projected CRS
        buf_geom = centroid_geom.buffer(radius, 12)
        buf_geom.transform(proj_to_orig)
        
        # Create new feature based on origin
        out_f = QgsFeature(res_layer.fields())
        # Copy attributes
        attrs = f.attributes()
        attrs.extend([radius, final_filling, found])
        out_f.setAttributes(attrs)
        out_f.setGeometry(buf_geom)
        
        out_features.append(out_f)
        
    res_pr.addFeatures(out_features)
    res_layer.updateExtents()
    
    return res_layer

