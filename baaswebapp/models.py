
class ModelHelpers:
    NULL_STRING = '------'
    UNKNOWN = ' Unknown'

    @classmethod
    def getUnknown(cls):
        return cls.objects.get(name=ModelHelpers.UNKNOWN)

    @classmethod
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
    def getDictObjectsId(cls):
        return {item.name.lower(): item.id for item in cls.getObjects()}

    @classmethod
    def getUnknownKey(cls):
        return cls.objects.get(name=ModelHelpers.UNKNOWN)

    @classmethod
    def returnFormatedItem(cls, asDict, id, name):
        if asDict:
            return {'name': name, 'value': id}
        else:
            return (id, name)

    @classmethod
    def getSelectList(cls, addNull=False, asDict=False):
        return cls._getSelectList(cls.getObjects(),
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

    @classmethod
    def getForeignModels(cls):
        if hasattr(cls, 'foreignModelLabels'):
            return cls.foreignModelLabels
        else:
            return {}

    @classmethod
    def getForeignModelsLabels(cls):
        if hasattr(cls, 'foreignModelLabels'):
            return list(cls.foreignModelLabels.values())
        else:
            return []

    @classmethod
    def generateFormKwargsChoices(cls, initialValues):
        dictModelLabel = cls.getForeignModels()
        dictKwargsChoices = {dictModelLabel[model]: model.getSelectList()
                             for model in dictModelLabel}
        dictKwargsChoices['initial'] = initialValues
        return dictKwargsChoices

    @classmethod
    def extractValueModelChoicesFromKwargs(cls, kwargs):
        modelValues = {}
        for label in cls.getForeignModelsLabels():
            modelValues[label] = cls.extractTagsFromKwargs(kwargs, label)
        return modelValues

    @classmethod
    def extractTagsFromKwargs(cls, kwargs, label):
        values = None
        if label in kwargs:
            values = kwargs[label]
            kwargs.pop(label, None)
        else:
            pass  # TODO: Assert !!
        return values

    @classmethod
    def getValueFromRequestOrArray(cls, request, values,
                                   label, intValue=False, floatValue=False,
                                   returnNoneIfEmpty=False):
        if label in values:
            return values[label]
        else:
            if label in request.POST:
                value = request.POST.get(label, None)
                returnNoneIfEmpty = True if intValue else returnNoneIfEmpty
                returnNoneIfEmpty = True if floatValue else returnNoneIfEmpty
                if returnNoneIfEmpty and value == '':
                    return None
                if intValue:
                    return int(value)
                if floatValue:
                    return float(value)
                return value
            else:
                return None

    @classmethod
    def preloadValues(cls, requestValues):
        values = {}
        foreignModels = cls.getForeignModels()
        for model in foreignModels:
            label = foreignModels[model]
            id = requestValues.get(label, None)
            if id:
                values[label] = model.objects.get(pk=requestValues[label])
            else:
                values[label] = None
        return values

    def getKey(self):
        return self.getName()

    def getName(self):
        return self.name

    def __str__(self):
        return self.getName()

    @classmethod
    def generateDataPointId(cls, level, evaluation,
                            reference, unit):
        return 'data-point-{}-{}-{}-{}'.format(
            level, evaluation.id,
            reference.id, unit.id)

    @classmethod
    def setDataPoint(cls, reference, evaluation, unit, value):
        dataPoint = cls.objects.filter(
            evaluation=evaluation,
            reference=reference,
            unit=unit).all()
        if not dataPoint:
            cls.objects.create(
                evaluation=evaluation,
                reference=reference,
                unit=unit,
                value=value)
        else:
            dataPoint[0].value = value
            dataPoint[0].save()
            # This should not happen, but in that case, remove items
            for i in range(1, len(dataPoint)):
                dataPoint[i].delete()

    @classmethod
    def getDataPoints(cls, evaluation):
        return cls.objects \
                  .filter(evaluation=evaluation)

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
        return [{'id': id, 'name': values[id]} for id in values]
