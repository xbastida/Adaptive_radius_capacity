# -*- coding: utf-8 -*-
from qgis.core import QgsApplication
from .AdaptiveRadiusCapacity_provider import AdaptiveRadiusCapacityProvider

class AdaptiveRadiusCapacityPlugin(object):
    """Clase principal para el plugin de capacidad adaptativa."""
    def __init__(self, iface):
        self.iface = iface
        self.provider = None

    def initProcessing(self):
        self.provider = AdaptiveRadiusCapacityProvider()
        QgsApplication.processingRegistry().addProvider(self.provider)

    def initGui(self):
        self.initProcessing()

    def unload(self):
        if self.provider:
            QgsApplication.processingRegistry().removeProvider(self.provider)