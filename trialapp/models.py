# Create your models here.
from django.db import models


class ModelHelpers:
    NULL_STRING = '------'

    @classmethod
    def getObjects(cls):
        return cls.objects.all().order_by('name')

    @classmethod
    def returnFormatedItem(self, asDict, id, name):
        if asDict:
            return {'name': name, 'value': id}
        else:
            return (id, name)

    @classmethod
    def getSelectList(cls, addNull=False, asDict=False):
        theList = []
        for item in cls.getObjects():
            theList.append(cls.returnFormatedItem(asDict, item.id, item.name))

        if addNull:
            theList.insert(
                0,
                cls.returnFormatedItem(
                    asDict,
                    None,
                    ModelHelpers.NULL_STRING))

        return theList

    def __str__(self):
        return self.name


class Crop(models.Model, ModelHelpers):
    name = models.CharField(max_length=100)


class FieldTrial(models.Model, ModelHelpers):
    name = models.CharField(max_length=100)
