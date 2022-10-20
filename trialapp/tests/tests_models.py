from django.test import TestCase
from trialapp.models import FieldTrial, ModelHelpers, Crop,\
                            TrialDbInitialLoader


# Create your tests here.
class FieldAppTest(TestCase):

    VALUES = {}

    @classmethod
    def setUpTestData(cls):

        FieldAppTest.VALUES = TrialDbInitialLoader.initialTrialModelValues()
        TrialDbInitialLoader.loadInitialTrialValues()

        # for itemName in FieldAppTest.FIELD_TEST_LIST:
        #     FieldTrial.objects.create(name=itemName)

    def test_ModelHelpers(self):
        cropValues = FieldAppTest.VALUES[Crop]
        len_cropValues = len(cropValues)
        itemsFromObjectsAll = Crop.objects.all()
        len_itemsFromObjectsAll = len(itemsFromObjectsAll)
        for item in itemsFromObjectsAll:
            self.assertTrue(item.name in cropValues)

        itemsGetObjects = Crop.getObjects()
        len_itemsGetObjects = len(itemsFromObjectsAll)
        for item in itemsGetObjects:
            self.assertTrue(item.name in cropValues)

        self.assertEqual(len_itemsFromObjectsAll, len_itemsGetObjects)
        self.assertEqual(len_itemsGetObjects, len_cropValues)

        theList = Crop.getSelectList()
        self.assertEqual(len(theList), len_cropValues)
        self.assertTrue(theList[0][1] in cropValues)

        theList = Crop.getSelectList(addNull=True)
        self.assertEqual(len(theList), len_cropValues+1)
        self.assertEqual(theList[0][1], ModelHelpers.NULL_STRING)
        self.assertEqual(theList[0][0], None)

        theArray = Crop.getSelectList(asDict=True)
        self.assertEqual(len(theArray), len_cropValues)
        self.assertTrue(theArray[0]['name'] in cropValues)

    def checkExtract(self, label, values, **kwargs):
        valuesExtracted = ModelHelpers.extractTagsFromKwargs(kwargs, label)
        self.assertTrue(len(valuesExtracted) ==
                        len(values))
        for valueItem in values:
            found = False
            for valueExtratecItem in valuesExtracted:
                if valueItem.name == valueExtratecItem[1]:
                    found = True
                    break
            self.assertTrue(found)

    def test_FieldTrialModelHelpers(self):
        foreignModels = FieldTrial.getForeignModels()
        foreignLabels = FieldTrial.getForeignModelsLabels()
        expectedModels = FieldTrial.foreignModelLabels
        self.assertTrue(len(foreignModels) == len(foreignLabels))
        self.assertTrue(len(list(expectedModels.values())) ==
                        len(foreignLabels))

        # Testing functions to create select choices for forms
        # for classes that has foreign keys
        crops = Crop.getObjects()
        selectListCrop = Crop.getSelectList()
        labelCrop = foreignModels[Crop]
        self.checkExtract(labelCrop, crops, crop=selectListCrop)

        # lets test for the whole class like FieldTrial
        # Let´s first generate the choices
        initialValues = {'field_trial_id': 66}
        dictKwargs = FieldTrial.generateFormKwargsChoices(initialValues)
        # check if all the key foreing keys are in + initial
        for label in foreignLabels:
            self.assertTrue(label in dictKwargs)
        self.assertTrue('initial' in dictKwargs)
        self.assertTrue(dictKwargs['initial']['field_trial_id'] ==
                        initialValues['field_trial_id'])
        # let´s emulate we passed it to a form and we extract them
        modelValues = FieldTrial.extractValueModelChoicesFromKwargs(
            dictKwargs)
        for model in foreignModels:
            labelModel = foreignModels[model]
            self.assertTrue(labelModel in modelValues)
            valuesModel = model.getObjects()
            dictKwargValues = {labelModel: modelValues[labelModel]}
            self.checkExtract(labelModel, valuesModel,
                              **dictKwargValues)
        self.assertFalse('initial' in modelValues)
