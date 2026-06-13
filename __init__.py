# -*- coding: utf-8 -*-
"""
hoverGeoPhoto – QGIS 4.0 plugin: show photo on point hover
"""

from qgis.core import QgsApplication
from .plugin import hoverGeoPhoto


def classFactory(iface):
    """Required plugin entry point."""
    return hoverGeoPhoto(iface)