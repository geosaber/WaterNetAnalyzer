from qgis.core import QgsProcessing
from qgis.core import QgsProcessingAlgorithm
from qgis.core import QgsProcessingMultiStepFeedback
from qgis.core import QgsProcessingParameterVectorLayer
from qgis.core import QgsProcessingParameterFeatureSink
import processing


class UpstreamGauges(QgsProcessingAlgorithm):

    def shortHelpString(self):
        return self.tr(""" Workflow: 
        1. select one line segment.
        2. In the drop-down lists chose the neede input layers. 
        3. Click on \"Run\"
        
        """)

    def initAlgorithm(self, config=None):
        self.addParameter(QgsProcessingParameterVectorLayer('fliessgewaessernetz', 'Fliessgewaessernetz', types=[QgsProcessing.TypeVectorLine], defaultValue=None))
        self.addParameter(QgsProcessingParameterVectorLayer('teileinzugsgebiete', 'Teileinzugsgebiete', types=[QgsProcessing.TypeVectorPolygon], defaultValue=None))
        self.addParameter(QgsProcessingParameterVectorLayer('pegelnetz', 'Pegelnetz', types=[QgsProcessing.TypeVectorPoint], defaultValue=None))
        self.addParameter(QgsProcessingParameterFeatureSink('PegelImEinzugsgebiet', 'Pegel im Einzugsgebiet', type=QgsProcessing.TypeVectorAnyGeometry, createByDefault=True, defaultValue=None))

    def processAlgorithm(self, parameters, context, model_feedback):
        # Use a multi-step feedback, so that individual child algorithm progress reports are adjusted for the
        # overall progress through the model
        feedback = QgsProcessingMultiStepFeedback(4, model_feedback)
        results = {}
        outputs = {}

        # 2 Flow path upstream/downstream
        alg_params = {
            'INPUT_FIELD_ID': 'NET_ID',
            'INPUT_FIELD_NEXT': 'NET_TO',
            'INPUT_FIELD_PREV': 'NET_FROM',
            'INPUT_LAYER': parameters['fliessgewaessernetz'],
            'INPUT_Sect': 0
        }
        outputs['FlowPathUpstreamdownstream'] = processing.run('Water_Net_Analyzer:2 Flow path upstream/downstream', alg_params, context=context, feedback=feedback, is_child_algorithm=True)

        feedback.setCurrentStep(1)
        if feedback.isCanceled():
            return {}

        # Extract selected features
        alg_params = {
            'INPUT': parameters['fliessgewaessernetz'],
            'OUTPUT': QgsProcessing.TEMPORARY_OUTPUT
        }
        outputs['ExtractSelectedFeatures'] = processing.run('native:saveselectedfeatures', alg_params, context=context, feedback=feedback, is_child_algorithm=True)

        feedback.setCurrentStep(2)
        if feedback.isCanceled():
            return {}

        # Extract by location
        alg_params = {
            'INPUT': parameters['teileinzugsgebiete'],
            'INTERSECT': outputs['ExtractSelectedFeatures']['OUTPUT'],
            'PREDICATE': [1],
            'OUTPUT': QgsProcessing.TEMPORARY_OUTPUT
        }
        outputs['ExtractByLocation'] = processing.run('native:extractbylocation', alg_params, context=context, feedback=feedback, is_child_algorithm=True)

        feedback.setCurrentStep(3)
        if feedback.isCanceled():
            return {}

        # Extract by location
        alg_params = {
            'INPUT': parameters['pegelnetz'],
            'INTERSECT': outputs['ExtractByLocation']['OUTPUT'],
            'PREDICATE': [6],
            'OUTPUT': parameters['PegelImEinzugsgebiet']
        }
        outputs['ExtractByLocation'] = processing.run('native:extractbylocation', alg_params, context=context, feedback=feedback, is_child_algorithm=True)
        results['PegelImEinzugsgebiet'] = outputs['ExtractByLocation']['OUTPUT']
        return results

    def name(self):
        return 'Pegel im Einzugsgebiet'

    def displayName(self):
        return 'Pegel im Einzugsgebiet'

    def group(self):
        return ''

    def groupId(self):
        return ''

    def createInstance(self):
        return PegelImEinzugsgebiet()
