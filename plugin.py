# -*- coding: utf-8 -*-
"""
hoverGeoPhoto – Main plugin logic
"""

import os
from PyQt6.QtCore import (
    Qt, QEvent, QPoint, QTimer, QUrl, QObject
)
from PyQt6.QtGui import QPixmap, QAction, QIcon
from PyQt6.QtWidgets import QToolBar
from qgis.core import (
    QgsProject, QgsVectorLayer, Qgis, QgsSettings
)
from qgis.gui import QgsMapToolIdentify
from qgis.PyQt.QtNetwork import QNetworkAccessManager, QNetworkRequest

from .popup_widget import PhotoPopup
from .settings_dialog import SettingsDialog


class HoverPhotoTool(QObject):
    """Handles mouse hover on canvas, identifies point features and shows photo popup."""

    def __init__(self, canvas, parent=None):
        super().__init__(parent)
        self.canvas = canvas
        self.enabled = False
        self.target_layer = None
        self.photo_field = "photo"
        self.popup = PhotoPopup(canvas)
        self.identify_tool = QgsMapToolIdentify(canvas)
        self._hover_timer = QTimer()
        self._hover_timer.setSingleShot(True)
        self._hover_timer.setInterval(80)
        self._hover_timer.timeout.connect(self._on_hover_timeout)
        self._current_feature_id = None
        self._pending_url = None
        self._network_manager = QNetworkAccessManager()
        self._network_manager.finished.connect(self._on_image_fetched)

    def set_enabled(self, enabled):
        self.enabled = enabled
        if not enabled:
            self.popup.hide()
            self._current_feature_id = None
            self._hover_timer.stop()
        else:
            viewport = self.canvas.viewport()
            viewport.installEventFilter(self)

    def set_target_layer(self, layer):
        if isinstance(layer, QgsVectorLayer) and layer.geometryType() == Qgis.GeometryType.Point:
            self.target_layer = layer
        else:
            self.target_layer = None
        self.popup.hide()
        self._current_feature_id = None

    def set_photo_field(self, field_name):
        self.photo_field = field_name

    def eventFilter(self, obj, event):
        if not self.enabled or not self.target_layer:
            return False
        if event.type() == QEvent.Type.MouseMove:
            self._last_pos = event.pos()
            self._hover_timer.start()
        elif event.type() == QEvent.Type.Leave:
            self.popup.hide()
            self._current_feature_id = None
            self._hover_timer.stop()
        return False

    def _on_hover_timeout(self):
        if not self.enabled or not self.target_layer:
            return
        pos = self._last_pos
        results = self.identify_tool.identify(
            pos.x(), pos.y(),
            QgsMapToolIdentify.IdentifyMode.TopDownAll,
            QgsMapToolIdentify.VectorLayer
        )
        if not results:
            self.popup.hide()
            self._current_feature_id = None
            return
        target_id = self.target_layer.id()
        feature = None
        for res in results:
            if res.mLayer.id() == target_id:
                feature = res.mFeature
                break
        if not feature or not feature.isValid():
            self.popup.hide()
            self._current_feature_id = None
            return
        if feature.id() == self._current_feature_id:
            return
        self._current_feature_id = feature.id()
        idx = self.target_layer.fields().indexFromName(self.photo_field)
        if idx == -1:
            self.popup.hide()
            return
        photo_value = feature.attribute(idx)
        if not photo_value or str(photo_value).strip() == "":
            self.popup.hide()
            return
        photo_path = str(photo_value).strip()
        global_cursor = self.canvas.mapToGlobal(pos)
        self.popup.show_at(global_cursor)
        self._load_image(photo_path)

    def _load_image(self, path_or_url):
        self.popup.show_loading()
        if path_or_url.startswith(('http://', 'https://')):
            url = QUrl(path_or_url)
            if not url.isValid():
                self.popup.show_error("Invalid URL")
                return
            request = QNetworkRequest(url)
            self._pending_url = url.toString()
            self._network_manager.get(request)
        else:
            if not os.path.isabs(path_or_url):
                project = QgsProject.instance()
                base = os.path.dirname(project.fileName()) if project.fileName() else ""
                if base:
                    path_or_url = os.path.join(base, path_or_url)
            if os.path.exists(path_or_url):
                pixmap = QPixmap(path_or_url)
                if not pixmap.isNull():
                    self.popup.set_image(pixmap)
                else:
                    self.popup.show_error("Invalid image file")
            else:
                self.popup.show_error("File not found")

    def _on_image_fetched(self, reply):
        if reply.error():
            self.popup.show_error(f"Network error: {reply.errorString()}")
            reply.deleteLater()
            return
        url = reply.url().toString()
        if url != self._pending_url:
            reply.deleteLater()
            return
        data = reply.readAll()
        pixmap = QPixmap()
        if pixmap.loadFromData(data):
            self.popup.set_image(pixmap)
        else:
            self.popup.show_error("Failed to load image")
        reply.deleteLater()
        self._pending_url = None


class hoverGeoPhoto:
    def __init__(self, iface):
        self.iface = iface
        self.action = None
        self.hover_tool = None
        self.settings = QgsSettings()

    def initGui(self):
        existing_toolbar = self.iface.mainWindow().findChild(QToolBar, "hoverGeoPhotoToolbar")
        if existing_toolbar:
            existing_toolbar.deleteLater()

        self.toolbar = QToolBar("hoverGeoPhoto")
        self.toolbar.setObjectName("hoverGeoPhotoToolbar")
        self.toolbar.setWindowTitle("hoverGeoPhoto")

        self.action = QAction("📷 hoverGeoPhoto", self.toolbar)
        self.action.setCheckable(True)
        self.action.setChecked(False)
        self.action.triggered.connect(self.on_action_triggered)
        self.toolbar.addAction(self.action)

        self.iface.mainWindow().addToolBar(self.toolbar)

        self.hover_tool = HoverPhotoTool(self.iface.mapCanvas())
        self.hover_tool.set_enabled(False)

        self.load_settings()

    def unload(self):
        if self.hover_tool:
            self.hover_tool.set_enabled(False)
            viewport = self.iface.mapCanvas().viewport()
            if viewport:
                viewport.removeEventFilter(self.hover_tool)
        if self.toolbar:
            self.toolbar.deleteLater()

    def on_action_triggered(self, checked):
        dlg = SettingsDialog(self.iface, self.iface.mainWindow())
        dlg.set_settings(
            enabled=self.hover_tool.enabled,
            layer_id=self.hover_tool.target_layer.id() if self.hover_tool.target_layer else "",
            photo_field=self.hover_tool.photo_field
        )
        if dlg.exec():
            new_settings = dlg.get_settings()
            self.apply_settings(new_settings)

        self.action.setChecked(self.hover_tool.enabled)

    def apply_settings(self, settings):
        enabled = settings["enabled"]
        layer_id = settings["layer_id"]
        photo_field = settings["photo_field"] or "photo"

        layer = None
        if layer_id:
            layer = QgsProject.instance().mapLayer(layer_id)
        self.hover_tool.set_target_layer(layer)
        self.hover_tool.set_photo_field(photo_field)
        self.hover_tool.set_enabled(enabled)

        self.settings.setValue("hoverGeoPhoto/enabled", enabled)
        self.settings.setValue("hoverGeoPhoto/layer_id", layer_id if layer_id else "")
        self.settings.setValue("hoverGeoPhoto/photo_field", photo_field)

        if enabled and not layer:
            self.iface.messageBar().pushMessage(
                "hoverGeoPhoto", "No point layer selected. Hover preview disabled.",
                level=Qgis.Warning, duration=3
            )
            self.hover_tool.set_enabled(False)
            self.action.setChecked(False)

    def load_settings(self):
        enabled = self.settings.value("hoverGeoPhoto/enabled", False, type=bool)
        layer_id = self.settings.value("hoverGeoPhoto/layer_id", "")
        photo_field = self.settings.value("hoverGeoPhoto/photo_field", "photo")
        self.apply_settings({
            "enabled": enabled,
            "layer_id": layer_id,
            "photo_field": photo_field
        })