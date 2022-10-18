# Create your models here.
from django.db import models


class ModelHelpers:
    NULL_STRING = '------'

    @staticmethod
    def createSelectList(objects, addNull=False):
        theList = [(item.id, item.name) for item in objects]
        if addNull:
            theList.insert(0, (None, ModelHelpers.NULL_STRING))
        return theList

    @staticmethod
    def getSelectedListAsArray(objects):
        return [{'name': item.name, 'value': item.id} for item in objects]


class FieldTrial(models.Model):
    name = models.CharField(max_length=100)

    def __str__(self):
        return self.name

    @staticmethod
    def getObjects():
        return FieldTrial.objects.all().order_by('name')

    @staticmethod
    def getSelectedList(addNull=False):
        return ModelHelpers.createSelectList(
            FieldTrial.getObjects(),
            addNull=addNull)

    @staticmethod
    def getSelectedListAsArray():
        return ModelHelpers.getSelectedListAsArray(FieldTrial.getObjects())
