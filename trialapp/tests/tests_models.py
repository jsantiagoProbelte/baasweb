from django.test import TestCase
from trialapp.models import FieldTrial, ModelHelpers


# Create your tests here.
class FieldAppTest(TestCase):

    FIELD_TEST_LIST = ['Trial 1', 'Trial 2']

    @classmethod
    def setUpTestData(cls):

        for itemName in FieldAppTest.FIELD_TEST_LIST:
            FieldTrial.objects.create(name=itemName)

    def test_TrendsModels(self):
        index = 0
        for item in FieldTrial.objects.all():
            self.assertEqual(item.name, FieldAppTest.FIELD_TEST_LIST[index])
            index += 1

        index2 = 0
        for item in FieldTrial.getObjects():
            self.assertEqual(item.name, FieldAppTest.FIELD_TEST_LIST[index2])
            index2 += 1
        self.assertEqual(index, index2)
        self.assertEqual(index2, len(FieldAppTest.FIELD_TEST_LIST))

        theList = FieldTrial.getSelectedList()
        self.assertEqual(len(theList), len(FieldAppTest.FIELD_TEST_LIST))
        self.assertEqual(theList[0][1], FieldAppTest.FIELD_TEST_LIST[0])

        theList = FieldTrial.getSelectedList(addNull=True)
        self.assertEqual(len(theList), len(FieldAppTest.FIELD_TEST_LIST)+1)
        self.assertEqual(theList[0][1], ModelHelpers.NULL_STRING)
        self.assertEqual(theList[0][0], None)

        theArray = FieldTrial.getSelectedListAsArray()
        self.assertEqual(len(theArray), len(FieldAppTest.FIELD_TEST_LIST))
        self.assertEqual(theArray[0]['name'], FieldAppTest.FIELD_TEST_LIST[0])
