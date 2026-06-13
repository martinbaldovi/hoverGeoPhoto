# -*- coding: utf-8 -*-
"""
Settings dialog for hoverGeoPhoto
"""

from PyQt6.QtWidgets import (
    QDialog, QVBoxLayout, QHBoxLayout, QFormLayout,
    QComboBox, QCheckBox, QDialogButtonBox, QLabel,
    QPushButton
)
from PyQt6.QtCore import Qt
from qgis.core import QgsProject, QgsVectorLayer, Qgis


class SettingsDialog(QDialog):
    def __init__(self, iface, parent=None):
        super().__init__(parent)
        self.iface = iface
        self.setWindowTitle("Settings")
        self.setMinimumWidth(350)

        layout = QVBoxLayout(self)

        # Enable/disable checkbox
        self.enable_check = QCheckBox("Enable hover preview")
        layout.addWidget(self.enable_check)

        form_layout = QFormLayout()
        # Layer selection
        self.layer_combo = QComboBox()
        self.layer_combo.setToolTip("Select point layer")
        form_layout.addRow("Layer", self.layer_combo)

        # Path/URL Field selection
        self.field_combo = QComboBox()
        self.field_combo.setToolTip("Attribute containing photo path/URL")
        form_layout.addRow("Path/URL Field", self.field_combo)

        layout.addLayout(form_layout)

        # OK/Cancel buttons: centered and spanning full width
        button_box = QDialogButtonBox(QDialogButtonBox.StandardButton.Ok | QDialogButtonBox.StandardButton.Cancel)
        button_box.accepted.connect(self.accept)
        button_box.rejected.connect(self.reject)
        # Center buttons horizontally and allow button box to take full width
        button_box.setCenterButtons(True)
        layout.addWidget(button_box)

        # Populate layers initially
        self.populate_layers()

        # Connect layer change to auto-update fields
        self.layer_combo.currentIndexChanged.connect(self.on_layer_changed)

    def populate_layers(self):
        """Fill layer combobox with point layers."""
        self.layer_combo.blockSignals(True)
        self.layer_combo.clear()
        for layer in QgsProject.instance().mapLayers().values():
            if isinstance(layer, QgsVectorLayer) and layer.geometryType() == Qgis.GeometryType.Point:
                self.layer_combo.addItem(layer.name(), layer.id())
        if self.layer_combo.count() == 0:
            self.layer_combo.addItem("No point layers available", None)
        self.layer_combo.blockSignals(False)
        self.on_layer_changed()

    def on_layer_changed(self):
        """Auto-refresh fields when layer changes."""
        self.field_combo.clear()
        layer_id = self.layer_combo.currentData()
        if not layer_id:
            return
        layer = QgsProject.instance().mapLayer(layer_id)
        if not layer or not isinstance(layer, QgsVectorLayer):
            return
        for field in layer.fields():
            self.field_combo.addItem(field.name(), field.name())

    def get_settings(self):
        """Return current settings from dialog."""
        return {
            "enabled": self.enable_check.isChecked(),
            "layer_id": self.layer_combo.currentData(),
            "photo_field": self.field_combo.currentData()
        }

    def set_settings(self, enabled, layer_id, photo_field):
        """Set dialog controls from saved settings."""
        self.enable_check.setChecked(enabled)
        idx = self.layer_combo.findData(layer_id)
        if idx >= 0:
            self.layer_combo.setCurrentIndex(idx)
            field_idx = self.field_combo.findData(photo_field)
            if field_idx >= 0:
                self.field_combo.setCurrentIndex(field_idx)