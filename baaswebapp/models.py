
class ModelHelpers:
    NULL_STRING = '------'
    UNKNOWN = ' Unknown'

    @classmethod
    def getUnknown(cls):
        return cls.objects.get(name=ModelHelpers.UNKNOWN)

    def isUnknown(self):
        return self.name == ModelHelpers.UNKNOWN

    @classmethod
    def getObjects(cls):
        return cls.objects.all().order_by('name')

    @classmethod
    def findOrCreate(cls, **args):
        objs = cls.objects.filter(**args)
        if objs:
            return objs[0]
        else:
            return cls.objects.create(**args)

    @classmethod
    def returnFormatedItem(cls, asDict, id, name):
        if asDict:
            return {'name': name, 'value': id}
        else:
            return (id, name)

    @classmethod
    def getSelectList(cls, addNull=False, asDict=False):
        return cls._getSelectList(cls.getObjects().order_by('name'),
                                  addNull=addNull,
                                  asDict=asDict)

    @classmethod
    def _getSelectList(cls, items, addNull=False, asDict=False):
        theList = []
        for item in items:
            theList.append(cls.returnFormatedItem(
                asDict, item.id, item.getName()))

        if addNull:
            theList.insert(
                0,
                cls.returnFormatedItem(
                    asDict,
                    None,
                    ModelHelpers.NULL_STRING))

        return theList

    def getKey(self):
        return self.getName()

    def getName(self):
        return self.name

    def __str__(self):
        return self.getName()

    @classmethod
    def extractDistincValues(cls, results, tag_id, tag_name):
        values = {}
        for result in results:
            found = result[tag_id]
            name = result[tag_name]
            if name in [ModelHelpers.UNKNOWN, 'N/A']:
                continue
            if found not in values:
                values[found] = name
        dimensionsDic = [{'value': id, 'name': values[id]} for id in values]
        return dimensionsDic, list(values.keys())
