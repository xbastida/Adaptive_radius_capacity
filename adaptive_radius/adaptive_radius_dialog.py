from qgis.PyQt import QtWidgets
from qgis.PyQt.QtCore import Qt
from qgis.gui import QgsMapLayerComboBox, QgsFieldComboBox
from qgis.core import QgsMapLayerProxyModel

class AdaptiveRadiusDialog(QtWidgets.QDialog):
    def __init__(self, parent=None):
        super(AdaptiveRadiusDialog, self).__init__(parent)
        
        self.lang = "en"
        
        self.strings = {
            "en": {
                "title": "Adaptive Radius Calculator",
                "origins": "Origins Layer:",
                "cap_field": "Capacity Field (from Origins):",
                "cap_default": "Or fixed Capacity (if no field):",
                "targets": "Targets Layer:",
                "fill_field": "Filling Field (from Targets):",
                "fill_default": "Or fixed Filling (if no field):",
                "step": "Step (m):",
                "max_rad": "Max Radius (m):",
                "crs": "Projected CRS (Metric):"
            },
            "es": {
                "title": "Calculadora de Radio Adaptativo",
                "origins": "Capa de Orígenes:",
                "cap_field": "Campo de Capacidad (de Orígenes):",
                "cap_default": "O Capacidad fija (si no hay campo):",
                "targets": "Capa de Destinos:",
                "fill_field": "Campo de Llenado (de Destinos):",
                "fill_default": "O Llenado fijo (si no hay campo):",
                "step": "Paso (m):",
                "max_rad": "Radio Máximo (m):",
                "crs": "CRS Proyectado (Métrico):"
            }
        }
        
        self.setWindowTitle(self.strings["en"]["title"])
        self.resize(500, 480)
        
        layout = QtWidgets.QVBoxLayout(self)
        
        # Language Switcher
        lang_layout = QtWidgets.QHBoxLayout()
        self.lbl_lang = QtWidgets.QLabel("Language / Idioma:")
        lang_layout.addWidget(self.lbl_lang)
        self.combo_lang = QtWidgets.QComboBox(self)
        self.combo_lang.addItems(["English", "Español"])
        self.combo_lang.currentIndexChanged.connect(self.update_labels)
        lang_layout.addWidget(self.combo_lang)
        layout.addLayout(lang_layout)
        
        # Separation
        layout.addWidget(QtWidgets.QFrame(frameShape=QtWidgets.QFrame.HLine))
        
        # Origins layer
        self.lbl_origins = QtWidgets.QLabel(self.strings["en"]["origins"])
        self.combo_origins = QgsMapLayerComboBox(self)
        self.combo_origins.setFilters(QgsMapLayerProxyModel.VectorLayer)
        layout.addWidget(self.lbl_origins)
        layout.addWidget(self.combo_origins)
        
        # Capacity field
        self.lbl_cap_field = QtWidgets.QLabel(self.strings["en"]["cap_field"])
        self.combo_cap_field = QgsFieldComboBox(self)
        self.combo_cap_field.setAllowEmptyFieldName(True)
        layout.addWidget(self.lbl_cap_field)
        layout.addWidget(self.combo_cap_field)
        self.combo_origins.layerChanged.connect(self.combo_cap_field.setLayer)
        if self.combo_origins.currentLayer():
            self.combo_cap_field.setLayer(self.combo_origins.currentLayer())
            
        # Capacity default (global)
        cap_def_layout = QtWidgets.QHBoxLayout()
        self.lbl_cap_def = QtWidgets.QLabel(self.strings["en"]["cap_default"])
        cap_def_layout.addWidget(self.lbl_cap_def)
        self.spin_cap_def = QtWidgets.QDoubleSpinBox(self)
        self.spin_cap_def.setRange(0.0, 10000000.0)
        self.spin_cap_def.setValue(100.0)
        cap_def_layout.addWidget(self.spin_cap_def)
        layout.addLayout(cap_def_layout)
        
        # Separation
        layout.addWidget(QtWidgets.QFrame(frameShape=QtWidgets.QFrame.HLine))

        # Targets layer
        self.lbl_targets = QtWidgets.QLabel(self.strings["en"]["targets"])
        self.combo_targets = QgsMapLayerComboBox(self)
        self.combo_targets.setFilters(QgsMapLayerProxyModel.VectorLayer)
        layout.addWidget(self.lbl_targets)
        layout.addWidget(self.combo_targets)
        
        # Filling field
        self.lbl_fill_field = QtWidgets.QLabel(self.strings["en"]["fill_field"])
        self.combo_fill_field = QgsFieldComboBox(self)
        self.combo_fill_field.setAllowEmptyFieldName(True)
        layout.addWidget(self.lbl_fill_field)
        layout.addWidget(self.combo_fill_field)
        self.combo_targets.layerChanged.connect(self.combo_fill_field.setLayer)
        if self.combo_targets.currentLayer():
            self.combo_fill_field.setLayer(self.combo_targets.currentLayer())
            
        # Filling default (global)
        fill_def_layout = QtWidgets.QHBoxLayout()
        self.lbl_fill_def = QtWidgets.QLabel(self.strings["en"]["fill_default"])
        fill_def_layout.addWidget(self.lbl_fill_def)
        self.spin_fill_def = QtWidgets.QDoubleSpinBox(self)
        self.spin_fill_def.setRange(0.0, 10000000.0)
        self.spin_fill_def.setValue(1.0)
        fill_def_layout.addWidget(self.spin_fill_def)
        layout.addLayout(fill_def_layout)
        
        # Separation
        layout.addWidget(QtWidgets.QFrame(frameShape=QtWidgets.QFrame.HLine))
        
        # Step
        step_layout = QtWidgets.QHBoxLayout()
        self.lbl_step = QtWidgets.QLabel(self.strings["en"]["step"])
        step_layout.addWidget(self.lbl_step)
        self.spin_step = QtWidgets.QDoubleSpinBox(self)
        self.spin_step.setRange(1.0, 10000.0)
        self.spin_step.setValue(20.0)
        step_layout.addWidget(self.spin_step)
        layout.addLayout(step_layout)
        
        # Max Radius
        max_layout = QtWidgets.QHBoxLayout()
        self.lbl_max = QtWidgets.QLabel(self.strings["en"]["max_rad"])
        max_layout.addWidget(self.lbl_max)
        self.spin_max = QtWidgets.QDoubleSpinBox(self)
        self.spin_max.setRange(10.0, 500000.0)
        self.spin_max.setValue(10000.0)
        max_layout.addWidget(self.spin_max)
        layout.addLayout(max_layout)

        # Projected CRS
        crs_layout = QtWidgets.QHBoxLayout()
        self.lbl_crs = QtWidgets.QLabel(self.strings["en"]["crs"])
        crs_layout.addWidget(self.lbl_crs)
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

    def update_labels(self):
        idx = self.combo_lang.currentIndex()
        self.lang = "es" if idx == 1 else "en"
        s = self.strings[self.lang]
        
        self.setWindowTitle(s["title"])
        self.lbl_origins.setText(s["origins"])
        self.lbl_cap_field.setText(s["cap_field"])
        self.lbl_cap_def.setText(s["cap_default"])
        
        self.lbl_targets.setText(s["targets"])
        self.lbl_fill_field.setText(s["fill_field"])
        self.lbl_fill_def.setText(s["fill_default"])
        
        self.lbl_step.setText(s["step"])
        self.lbl_max.setText(s["max_rad"])
        self.lbl_crs.setText(s["crs"])
