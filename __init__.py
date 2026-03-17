# -*- coding: utf-8 -*-
def classFactory(iface):
    from .main_plugin import AdaptiveRadiusCapacityPlugin
    return AdaptiveRadiusCapacityPlugin(iface)