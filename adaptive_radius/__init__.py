def classFactory(iface):
    """Load AdaptiveRadius class from file AdaptiveRadius.
    
    :param iface: A QGIS interface instance.
    :type iface: QgsInterface
    """
    from .adaptive_radius import AdaptiveRadiusPlugin
    return AdaptiveRadiusPlugin(iface)
