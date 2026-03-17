# -*- coding: utf-8 -*-
from qgis.PyQt.QtCore import QCoreApplication, QVariant
from qgis.core import (QgsProcessing, QgsFeature, QgsField, QgsFeatureSink,
                       QgsRectangle, QgsSpatialIndex, QgsWkbTypes,
                       QgsProcessingAlgorithm, QgsProcessingParameterFeatureSource,
                       QgsProcessingParameterFeatureSink, QgsProcessingParameterField,
                       QgsProcessingParameterNumber)

class AdaptiveRadiusCapacityAlgorithm(QgsProcessingAlgorithm):
    # Constantes de parámetros
    INPUT_MANZANAS = 'INPUT_MANZANAS'
    POB_FIELD = 'POB_FIELD'
    POB_FIXED = 'POB_FIXED'
    INPUT_INTERES = 'INPUT_INTERES'
    CAP_FIELD = 'CAP_FIELD'
    CAP_FIXED = 'CAP_FIXED'
    STEP_M = 'STEP_M'
    MAX_RADIUS = 'MAX_RADIUS'
    OUTPUT = 'OUTPUT'

    def initAlgorithm(self, config):
        self.addParameter(QgsProcessingParameterFeatureSource(self.INPUT_MANZANAS, self.tr('Capa de población a analizar'), [QgsProcessing.TypeVectorPolygon]))
        self.addParameter(QgsProcessingParameterField(self.POB_FIELD, self.tr('Campo de población objetivo'), parentLayerParameterName=self.INPUT_MANZANAS, optional=True))
        self.addParameter(QgsProcessingParameterNumber(self.POB_FIXED, self.tr('Población objetivo fija'), defaultValue=1.0))
        self.addParameter(QgsProcessingParameterFeatureSource(self.INPUT_INTERES, self.tr('Puntos de interés'), [QgsProcessing.TypeVectorPoint]))
        self.addParameter(QgsProcessingParameterField(self.CAP_FIELD, self.tr('Campo de capacidad'), parentLayerParameterName=self.INPUT_INTERES, optional=True))
        self.addParameter(QgsProcessingParameterNumber(self.CAP_FIXED, self.tr('Capacidad objetivo fija'), defaultValue=400.0))
        self.addParameter(QgsProcessingParameterNumber(self.STEP_M, self.tr('Incremento (m)'), defaultValue=50.0))
        self.addParameter(QgsProcessingParameterNumber(self.MAX_RADIUS, self.tr('Radio máx (m)'), defaultValue=5000.0))
        self.addParameter(QgsProcessingParameterFeatureSink(self.OUTPUT, self.tr('Capa de salida')))

    def processAlgorithm(self, parameters, context, feedback):
        source_manzanas = self.parameterAsSource(parameters, self.INPUT_MANZANAS, context)
        pob_field = self.parameterAsString(parameters, self.POB_FIELD, context)
        pob_fixed = self.parameterAsDouble(parameters, self.POB_FIXED, context)
        source_interes = self.parameterAsSource(parameters, self.INPUT_INTERES, context)
        cap_field = self.parameterAsString(parameters, self.CAP_FIELD, context)
        cap_fixed = self.parameterAsDouble(parameters, self.CAP_FIXED, context)
        step = self.parameterAsDouble(parameters, self.STEP_M, context)
        max_r = self.parameterAsDouble(parameters, self.MAX_RADIUS, context)

        spatial_index = QgsSpatialIndex(source_manzanas.getFeatures())
        out_fields = source_interes.fields()
        out_fields.append(QgsField("radius_m", QVariant.Double))
        out_fields.append(QgsField("final_fill", QVariant.Double))

        (sink, dest_id) = self.parameterAsSink(parameters, self.OUTPUT, context, out_fields, QgsWkbTypes.Polygon, source_interes.sourceCrs())

        for current, feat in enumerate(source_interes.getFeatures()):
            if feedback.isCanceled(): break
            capacity = feat[cap_field] if cap_field else cap_fixed
            point = feat.geometry().asPoint()
            radius = step
            fill = 0.0
            while radius <= max_r:
                ids = spatial_index.intersects(QgsRectangle(point.x()-radius, point.y()-radius, point.x()+radius, point.y()+radius))
                fill = sum([source_manzanas.getFeature(i)[pob_field] if pob_field else pob_fixed for i in ids if point.distance(source_manzanas.getFeature(i).geometry().centroid().asPoint()) <= radius])
                if fill >= capacity: break
                radius += step
            out_feat = QgsFeature(out_fields)
            out_feat.setGeometry(feat.geometry().buffer(radius, 30))
            out_feat.setAttributes(feat.attributes() + [radius, fill])
            sink.addFeature(out_feat, QgsFeatureSink.FastInsert)
        return {self.OUTPUT: dest_id}

    def name(self): return 'AdaptiveRadiusCapacity'
    def displayName(self): return self.tr('Buffer por Capacidad')
    def group(self): return self.tr('Análisis Urbano')
    def groupId(self): return 'urbantech'
    def tr(self, string): return QCoreApplication.translate('AdaptiveRadiusCapacity', string)
    def createInstance(self): return AdaptiveRadiusCapacityAlgorithm()