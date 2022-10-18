from django.test import TestCase
from trialapp.models import FieldTrial, ModelHelpers, Crop


# Create your tests here.
class FieldAppTest(TestCase):

    FIELD_TEST_LIST = ['Trial 1', 'Trial 2']
    CROPS = ['fresa', 'patata']

    @classmethod
    def setUpTestData(cls):

        for itemName in FieldAppTest.CROPS:
            Crop.objects.create(name=itemName)

        for itemName in FieldAppTest.FIELD_TEST_LIST:
            FieldTrial.objects.create(name=itemName)

    def test_ModelHelpers(self):
        index = 0
        for item in Crop.objects.all():
            self.assertEqual(item.name, FieldAppTest.CROPS[index])
            index += 1

        index2 = 0
        for item in Crop.getObjects():
            self.assertEqual(item.name, FieldAppTest.CROPS[index2])
            index2 += 1
        self.assertEqual(index, index2)
        self.assertEqual(index2, len(FieldAppTest.CROPS))

        theList = Crop.getSelectList()
        self.assertEqual(len(theList), len(FieldAppTest.CROPS))
        self.assertEqual(theList[0][1], FieldAppTest.CROPS[0])

        theList = Crop.getSelectList(addNull=True)
        self.assertEqual(len(theList), len(FieldAppTest.CROPS)+1)
        self.assertEqual(theList[0][1], ModelHelpers.NULL_STRING)
        self.assertEqual(theList[0][0], None)

        theArray = Crop.getSelectList(asDict=True)
        self.assertEqual(len(theArray), len(FieldAppTest.CROPS))
        self.assertEqual(theArray[0]['name'], FieldAppTest.CROPS[0])

    def test_TrialsModels(self):
        trials = FieldTrial.getObjects()
        for item in trials:
            self.assertTrue(item.name in FieldAppTest.FIELD_TEST_LIST)
        self.assertTrue(len(trials) == len(FieldAppTest.FIELD_TEST_LIST))
