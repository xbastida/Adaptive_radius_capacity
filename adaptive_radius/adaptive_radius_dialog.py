from qgis.PyQt import QtWidgets
from qgis.PyQt.QtCore import Qt
from qgis.gui import QgsMapLayerComboBox, QgsFieldComboBox
from qgis.core import QgsMapLayerProxyModel

class AdaptiveRadiusDialog(QtWidgets.QDialog):
    def __init__(self, parent=None):
        super(AdaptiveRadiusDialog, self).__init__(parent)
        self.setWindowTitle("Adaptive Radius Calculator")
        self.resize(450, 350)
        
        layout = QtWidgets.QVBoxLayout(self)
        
        # Origins layer
        self.combo_origins = QgsMapLayerComboBox(self)
        self.combo_origins.setFilters(QgsMapLayerProxyModel.VectorLayer)
        layout.addWidget(QtWidgets.QLabel("Origins Layer:"))
        layout.addWidget(self.combo_origins)
        
        # Capacity field
        self.combo_cap_field = QgsFieldComboBox(self)
        layout.addWidget(QtWidgets.QLabel("Capacity Field (from Origins):"))
        layout.addWidget(self.combo_cap_field)
        self.combo_origins.layerChanged.connect(self.combo_cap_field.setLayer)
        if self.combo_origins.currentLayer():
            self.combo_cap_field.setLayer(self.combo_origins.currentLayer())
            
        # Targets layer
        self.combo_targets = QgsMapLayerComboBox(self)
        self.combo_targets.setFilters(QgsMapLayerProxyModel.VectorLayer)
        layout.addWidget(QtWidgets.QLabel("Targets Layer:"))
        layout.addWidget(self.combo_targets)
        
        # Filling field
        self.combo_fill_field = QgsFieldComboBox(self)
        layout.addWidget(QtWidgets.QLabel("Filling Field (from Targets):"))
        layout.addWidget(self.combo_fill_field)
        self.combo_targets.layerChanged.connect(self.combo_fill_field.setLayer)
        if self.combo_targets.currentLayer():
            self.combo_fill_field.setLayer(self.combo_targets.currentLayer())
            
        # Step
        step_layout = QtWidgets.QHBoxLayout()
        step_layout.addWidget(QtWidgets.QLabel("Step (m):"))
        self.spin_step = QtWidgets.QDoubleSpinBox(self)
        self.spin_step.setRange(1.0, 10000.0)
        self.spin_step.setValue(20.0)
        step_layout.addWidget(self.spin_step)
        layout.addLayout(step_layout)
        
        # Max Radius
        max_layout = QtWidgets.QHBoxLayout()
        max_layout.addWidget(QtWidgets.QLabel("Max Radius (m):"))
        self.spin_max = QtWidgets.QDoubleSpinBox(self)
        self.spin_max.setRange(10.0, 500000.0)
        self.spin_max.setValue(10000.0)
        max_layout.addWidget(self.spin_max)
        layout.addLayout(max_layout)

        # Projected CRS
        crs_layout = QtWidgets.QHBoxLayout()
        crs_layout.addWidget(QtWidgets.QLabel("Projected CRS (Metric):"))
        self.edit_crs = QtWidgets.QLineEdit("EPSG:25830", self)
        crs_layout.addWidget(self.edit_crs)
        layout.addLayout(crs_layout)
        
        # Buttons
        self.buttonBox = QtWidgets.QDialogButtonBox(
            QtWidgets.QDialogButtonBox.Ok | QtWidgets.QDialogButtonBox.Cancel,
            Qt.Horizontal, self)
        self.buttonBox.accepted.connect(self.accept)
        self.buttonBox.rejected.connect(self.reject)
        layout.addWidget(self.buttonBox)
