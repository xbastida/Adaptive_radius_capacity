import os
import tempfile
import traceback
from qgis.PyQt.QtCore import QSettings, QTranslator, QCoreApplication
from qgis.PyQt.QtGui import QIcon
from qgis.PyQt.QtWidgets import QAction, QMessageBox

from qgis.core import (
    QgsProject,
    QgsVectorLayer,
    QgsVectorFileWriter,
    Qgis
)

from .adaptive_radius_dialog import AdaptiveRadiusDialog
from .core_logic import compute_adaptive_radius

class AdaptiveRadiusPlugin:
    def __init__(self, iface):
        self.iface = iface
        self.plugin_dir = os.path.dirname(__file__)
        self.actions = []
        self.menu = "Adaptive Radius"

    def initGui(self):
        icon_path = os.path.join(self.plugin_dir, 'icon.svg')
        self.action = QAction(QIcon(icon_path), "Compute Adaptive Radius...", self.iface.mainWindow())
        self.action.triggered.connect(self.run)
        self.iface.addToolBarIcon(self.action)
        self.iface.addPluginToMenu(self.menu, self.action)
        self.actions.append(self.action)

    def unload(self):
        for action in self.actions:
            self.iface.removePluginMenu(self.menu, action)
            self.iface.removeToolBarIcon(action)

    def run(self):
        dialog = AdaptiveRadiusDialog()
        result = dialog.exec_()
        
        if result == 1:
            origin_layer = dialog.combo_origins.currentLayer()
            target_layer = dialog.combo_targets.currentLayer()
            cap_field = dialog.combo_cap_field.currentField()
            fill_field = dialog.combo_fill_field.currentField()
            step_m = dialog.spin_step.value()
            max_m = dialog.spin_max.value()
            crs_str = dialog.edit_crs.text()
            
            if not origin_layer or not target_layer or not cap_field or not fill_field:
                QMessageBox.warning(self.iface.mainWindow(), "Error", "Please select valid layers and fields.")
                return
            
            # Show progress on QGIS MessageBar
            msgId = self.iface.messageBar().pushMessage("Adaptive Radius", "Computing buffer capacities... (QGIS may be unresponsive)", level=Qgis.Info)
            
            try:
                # Run the PyQGIS backend
                res_layer = compute_adaptive_radius(
                    origin_layer=origin_layer, 
                    target_layer=target_layer, 
                    capacity_col=cap_field, 
                    filling_col=fill_field, 
                    step_m=step_m,
                    max_radius_m=max_m,
                    projected_crs_str=crs_str
                )
                
                res_layer.setName(f"Adaptive Radii ({step_m}m step)")
                
                if res_layer.isValid():
                    QgsProject.instance().addMapLayer(res_layer)
                    self.iface.messageBar().pushMessage("Adaptive Radius", "Computation finished and layer added!", level=Qgis.Success)
                else:
                    QMessageBox.warning(self.iface.mainWindow(), "Error", "Failed to generate result layer.")
                    
            except Exception as e:
                self.iface.messageBar().pushMessage("Adaptive Radius", f"Error: {e}", level=Qgis.Critical)
                QMessageBox.critical(self.iface.mainWindow(), "Error", f"Failed to compute:\n{traceback.format_exc()}")
            finally:
                self.iface.messageBar().clearWidgets()
