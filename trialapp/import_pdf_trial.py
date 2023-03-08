import os
import django
import tabula
from dateutil.parser import parse
import shutil
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'baaswebapp.dev')
django.setup()

from baaswebapp.models import ModelHelpers  # noqa: E402
from trialapp.models import FieldTrial, Crop, Project, Objective, Plague,\
    Thesis, Replica, TrialAssessmentSet, AssessmentType, AssessmentUnit,\
    Evaluation, TrialStatus, TrialType  # noqa: E402
from trialapp.data_models import ReplicaData  # noqa: E402
from catalogue.models import Product  # noqa: E402


class TrialTags:
    SAMPLING_SIZE = 'Sample Size'
    CROP_CODE = 'Crop Code'
    PEST_CODE = 'Pest Code'
    RATING_DATE = 'Rating Date'
    ASSESSMENT_DATE = 'Assessment Date'
    CROP_STAGE = 'Crop Stage Majority'
    RATING_TYPE = 'Rating Type'
    ASSESSMENT_TYPE = 'Assessment Type'
    RATING_UNIT = 'Rating Unit'
    ASSESSMENT_UNIT = 'Assessment Unit'  # Assessment Unit/Min/Max
    INTERVAL = 'Trt-Eval Interval'
    KEY_TAGS = [RATING_DATE, SAMPLING_SIZE, RATING_TYPE, ASSESSMENT_TYPE,
                ASSESSMENT_DATE]
    TAGS = [RATING_DATE, CROP_STAGE, RATING_TYPE, RATING_UNIT, ASSESSMENT_UNIT,
            ASSESSMENT_TYPE, ASSESSMENT_DATE, INTERVAL, CROP_CODE, PEST_CODE]
    SAMPLING_SIZE_ES = 'Numero submuestras'
    CROP_CODE_ES = 'Código cultivo'
    PEST_CODE_ES = 'Código Plaga'
    RATING_DATE_ES = 'Fecha Valoración'
    CROP_STAGE_ES = 'Estado del cultivo Mayoritario/Min/Max'
    RATING_TYPE_ES = 'Descripción'
    RATING_UNIT_ES = 'Rating Unit'
    INTERVAL_ES = 'Trt-Eval Interval'
    KEY_TAGS_ES = [RATING_DATE_ES, SAMPLING_SIZE_ES, RATING_TYPE_ES]
    TAGS_ES = [RATING_DATE_ES, CROP_STAGE_ES, RATING_TYPE_ES, RATING_UNIT_ES,
               INTERVAL_ES, CROP_CODE_ES, PEST_CODE_ES]

    TAG_TYPES = [ASSESSMENT_TYPE, RATING_TYPE, RATING_TYPE_ES]
    TAG_DATES = [ASSESSMENT_DATE, RATING_DATE, RATING_DATE_ES]

    CROPS = {'CUMSA': 'cucumber', 'FRASS': 'Strawberry', 'PRNPS': 'Peach',
             'LACSA': 'Letuce'}  # Lactuca sativa
    PESTS = {'BOTRCI': 'botrytis', 'MONIFG': 'Moniliosis'}

    LANG_EN = 'EN'
    LANG_ES = 'ES'

    ALL_TAGS = {
        LANG_EN: TAGS,
        LANG_ES: TAGS_ES}

    ALL_KEY_TAGS = {
        LANG_EN: KEY_TAGS,
        LANG_ES: KEY_TAGS_ES}

    @classmethod
    def getTags(cls, language):
        return TrialTags.ALL_TAGS[language]

    @classmethod
    def getKeyTags(cls, language):
        return TrialTags.ALL_KEY_TAGS[language]

    @classmethod
    def getRateUnitTag(cls, language):
        if language == TrialTags.LANG_EN:
            return TrialTags.RATING_UNIT
        elif language == TrialTags.LANG_ES:
            return TrialTags.RATING_UNIT_ES

    @classmethod
    def getPestTag(cls, language):
        if language == TrialTags.LANG_EN:
            return TrialTags.PEST_CODE
        elif language == TrialTags.LANG_ES:
            return TrialTags.PEST_CODE_ES

    @classmethod
    def getCropTag(cls, language):
        if language == TrialTags.LANG_EN:
            return TrialTags.CROP_CODE
        elif language == TrialTags.LANG_ES:
            return TrialTags.CROP_CODE_ES

    @classmethod
    def getIntervalTag(cls, language):
        if language == TrialTags.LANG_EN:
            return TrialTags.INTERVAL
        elif language == TrialTags.LANG_ES:
            return TrialTags.INTERVAL_ES

    @classmethod
    def getStageTag(cls, language):
        if language == TrialTags.LANG_EN:
            return TrialTags.CROP_STAGE
        elif language == TrialTags.LANG_ES:
            return TrialTags.CROP_STAGE_ES


class PdfImportExport_using_based_class(Exception):
    pass


# Base class for common methods
class AssmtTable:
    _table = None
    _firstColumnName = None
    _numberRows = None
    _columns = None
    _numberColumns = None
    _trial = None
    _tagPositions = {}
    _correctPosition = 0
    _replicaDict = {}
    _indexfirstColumnWithValues = 1
    _columnReplicaNames = 0
    _firstRowValuesNames = 1
    _thesis = {}
    _createdThesis = []

    def __init__(self, table, trial, language=TrialTags.LANG_EN):
        self._table = table
        self._firstRowValuesNames = 1
        self._trial = trial
        self._columns = table.columns
        self._firstColumnName = self._table.columns[0]
        self._numberRows = len(self._table)
        self._numberColumns = len(self._columns)
        self._correctPosition = 0
        self._indexfirstColumnWithValues = 1
        self._columnReplicaNames = 0
        self._tagPositions = {}
        self._replicaDict = {}
        self._thesis = {}
        self._language = language

    def prepareThesis(self):
        for thesis in Thesis.getObjects(self._trial):
            joinName = thesis.name.replace(" ", "")
            self._thesis[joinName] = thesis

    def findOrCreateThesis(self, name, number):
        thesis = self.existThesis(name)
        if thesis is None:
            thesis = Thesis.findOrCreate(
                            name=name.strip(),
                            number=number,
                            field_trial=self._trial)
        return thesis

    def findOrCreateReplica(self, name, number, thesis):
        if 'ABCD' in name:
            name = name.replace('ABCD', '')
        name = name.strip()
        if name.isdigit() and len(name) == 3:
            return Replica.findOrCreate(
                            name=name,
                            number=number,
                            thesis=thesis)
        return None

    def extractReplicasNames(self, info):
        parts = info.split('\r')
        replicaIds = []
        lenParts = len(parts)
        if lenParts == 1:
            return []
        # First replica id, is in the first line,
        # we expect 3 numbers
        replicaIds.append(parts[0][-3:])
        # Explore the rest, but skip the last one, which indicates the Mean
        for i in range(1, lenParts-1):
            replicaIds.append(parts[i])
        return replicaIds

    def existThesis(self, newthesisname):
        return self._thesis.get(newthesisname.replace(" ", ""), None)

    def isValid(self):
        if self._indexfirstColumnWithValues is not None:
            return True
        else:
            return False

    def getValueAtRow(self, values, position):
        raise PdfImportExport_using_based_class()

    def findRowPosition(self, columnText, key):
        raise PdfImportExport_using_based_class()

    def getKeyTrialValues(self, model, tag, valuesDict):
        # Lets check in which row shows 'Crop Code'
        keyColumnValues = self._columns[self._indexfirstColumnWithValues]
        value = self.getTagPositionValue(keyColumnValues, tag, None)
        if value:
            if value in valuesDict:
                return model.objects.get(name__iexact=valuesDict[value])
            else:
                return model.findOrCreate(name=value)
        return None

    def getPest(self):
        if self._trial.plague.name != ModelHelpers.UNKNOWN:
            return

        pestCode = TrialTags.getPestTag(self._language)
        result = self.getKeyTrialValues(
            Plague, pestCode, TrialTags.PESTS)
        if result:
            self._trial.plague = result
            self._trial.save()

    def getCrop(self):
        if self._trial.crop.name != ModelHelpers.UNKNOWN:
            return
        cropCode = TrialTags.getCropTag(self._language)
        result = self.getKeyTrialValues(
            Crop, cropCode, TrialTags.CROPS)
        if result:
            self._trial.crop = result
            self._trial.save()

    def extractTableData(self):
        # Realize the headers are multiple lines
        # Let's extract the crop and pest
        self.findTagPositions()
        self.prepareThesis()
        self.getCrop()
        self.getPest()
        foundReplicas = self.extractThesis()
        if foundReplicas == 0:
            # This table does not contain replica data.
            # Better to scape..
            return False
        self.extractEvaluations()
        return True

    def getThesisIndex(self, thesisInfo):
        if thesisInfo[:2].isdigit():
            return int(thesisInfo[:2]), thesisInfo[2:]
        elif thesisInfo[:1].isdigit():
            return int(thesisInfo[:1]), thesisInfo[1:]
        else:
            return None, thesisInfo

    def getFirstReplica(self, thesisInfo):
        if thesisInfo[-3:].isdigit():
            return thesisInfo[-3:], thesisInfo[:-3]
        else:
            return None, thesisInfo

    def extractThesisInfo(self, thesisInfoLong):
        # There could be 3 components.
        # [Number][thesis name][replica number]\r[replica]\r...
        # '1PB001 12 mL/L'
        thesisInfo = thesisInfoLong.split('\r')[0]
        number, thesisInfo = self.getThesisIndex(thesisInfo)
        firstReplica, thesisInfo = self.getFirstReplica(thesisInfo)
        if 'ABCD' in thesisInfo:
            thesisInfo = thesisInfo.replace('ABCD', '')
        name = thesisInfo.strip()
        return number, name, firstReplica

    def getTagPositionValue(self, columnName, tag, default):
        position = self._tagPositions.get(tag, None)
        if position is None:
            return default
        return self.getValueAtRow(columnName, position)

    def findTagPositions(self):
        for tag in TrialTags.getTags(self._language):
            position = self.findRowPosition(self._firstColumnName, tag)
            if position is not None:
                self._tagPositions[tag] = position
        return

    def extractEvaluations(self):
        # Get some useful positions of tags
        for columnIndex in range(self._indexfirstColumnWithValues,
                                 self._numberColumns):
            columnName = self._columns[columnIndex]
            evaluation = self.extractEvaluationInfo(columnName)
            if evaluation is None:
                # Abort
                continue
            assessmentSet = self.extractAssessmentInfo(columnName)
            self.extractAssessmentData(
                columnName, evaluation, assessmentSet)

    def getValidDate(self, theDateStr):
        # check if this is date
        try:
            return parse(theDateStr, fuzzy=True)
        except ValueError:
            return None

    def correctDatePosition(self, columnName, dateTag):
        positionDate = self._tagPositions.get(dateTag, None)
        for i in range(1, positionDate):
            newPosition = positionDate - i
            theDateStr = self.getValueAtRow(columnName, newPosition)
            theDate = self.getValidDate(theDateStr)
            if theDate:
                self._correctPosition = i
                return theDate
        # we failed to find a date
        return None

    def getRatingDate(self, columnName):
        # we reset this correction, in the first value query per column
        # which is for date, because it is also the easier to identify
        # if we get it wrong
        self._correctPosition = 0
        theDateStr = None
        foundTag = None
        for dateTag in TrialTags.TAG_DATES:
            theDateStr = self.getTagPositionValue(
                columnName, dateTag, None)
            if theDateStr is not None:
                foundTag = dateTag
                break
        theDate = self.getValidDate(theDateStr)
        if theDate:
            return theDate
        return self.correctDatePosition(columnName, foundTag)

    def getCropStage(self, columnName):
        stageTag = TrialTags.getStageTag(self._language)
        return self.getTagPositionValue(
            columnName, stageTag, 'Undefined')

    def isColumnWithValues(self, columnName):
        value1 = self._table.loc[self._firstRowValuesNames, columnName]
        value2 = self._table.loc[self._firstRowValuesNames+1, columnName]
        if isinstance(value1, str) and isinstance(value2, str):
            return True
        return False

    def extractEvaluationInfo(self, columnName):
        # Validate that we have values in these column
        if not self.isColumnWithValues(columnName):
            return None

        # Each evaluation is in a different column
        theDate = self.getRatingDate(columnName)
        if theDate is None:
            # Abort
            return None

        stage = self.getCropStage(columnName)
        intervalTag = TrialTags.getIntervalTag(self._language)
        interval = self.getTagPositionValue(
            columnName, intervalTag, 'Unknown')
        if not interval:
            interval = "{}-({})".format(theDate, stage)

        return Evaluation.findOrCreate(
                name=interval,
                evaluation_date=theDate,
                field_trial=self._trial,
                crop_stage_majority=stage)

    def extractAssessmentInfo(self, columnName):
        # Each column may have different assessment type and units
        typeName = None
        for rateType in TrialTags.TAG_TYPES:
            typeName = self.getTagPositionValue(
                columnName, rateType, None)
            if typeName is not None:
                break
        if typeName is None:
            typeName = ModelHelpers.UNKNOWN
        type = AssessmentType.findOrCreate(name=typeName)

        rateUnit = TrialTags.getRateUnitTag(self._language)
        unitName = self.getTagPositionValue(
            columnName, rateUnit, ModelHelpers.UNKNOWN)
        unit = AssessmentUnit.findOrCreate(name=unitName)

        return TrialAssessmentSet.findOrCreate(
                type=type, unit=unit, field_trial=self._trial)

    def convertToFloat(self, decStr):
        try:
            return float(decStr)
        except ValueError:
            # Maybe there is a comma
            decPart = decStr.split(',')
            if len(decPart) > 1:
                puntStr = "{}.{}".format(decPart[0], decPart[1])
                return self.convertToFloat(puntStr)
            else:
                return None

    def saveDataPoint(self, value, evaluation, assessmentSet, replica):
        valueFloat = self.convertToFloat(value)
        if valueFloat is not None:
            ReplicaData.findOrCreate(
                value=self.convertToFloat(valueFloat),
                evaluation=evaluation,
                unit=assessmentSet,
                reference=replica)
        else:
            print('Cannot import value in {}-{}'.format(
                self._firstColumnName, replica))

    def cleanUp(self):
        for thesis in Thesis.getObjects(self._trial):
            for replica in Replica.getObjects(thesis):
                if replica.name.isdigit() and len(replica.name) == 3:
                    pass
                else:
                    replica.delete()
            if len(Replica.getObjects(thesis)) == 0:
                thesis.delete()


# Class for tables with multiple lines inside the header
class AssmtTableMultiLineHeader(AssmtTable):

    def __init__(self, table, trial, language=TrialTags.LANG_EN):
        super().__init__(table, trial, language=language)

    def findRowPosition(self, columnText, key):
        index = 0
        rows = columnText.split('\r')
        for row in rows:
            if key in row:
                return index
            index += 1
        return None

    def getValueAtRow(self, values, position):
        checkPosition = position - self._correctPosition
        # This above assumption is not correct
        # We may identify that we miss some value and then correct it
        # but it does not mean that we need to correct it for all the values
        componens = values.split('\r')
        if checkPosition < len(componens):
            return componens[checkPosition]
        return None

    def extractThesis(self):
        # Thesis are in first column. They look like this:
        # '1 PB00112 mL/L ABCD 106\r204\r301\r403\rMean ='
        # '[thesisnumber] [prod][dosis] [Replica1]\r[..]\r[Replica2]\rMean ='
        # Notice that there is no space between product and dosis
        # For the sake of identify thesis, we use put it together
        # Remember that first row is already the thesis
        foundReplicas = 0
        for index in range(1, self._numberRows):
            thesisInfo = self._table.loc[index, self._firstColumnName]
            number, name, firstReplicaName = self.extractThesisInfo(thesisInfo)
            if number is None:
                number = index
            thesis = self.findOrCreateThesis(name, number)

            # Check for replicas
            replicas = self.extractReplicasNames(thesisInfo)
            if not replicas:
                return 0
            self._replicaDict[number] = {}
            index = 1
            for replicaName in replicas:
                replica = self.findOrCreateReplica(
                    replicaName,
                    index,
                    thesis)
                if replica is not None:
                    self._replicaDict[number][index] = replica
                    index += 1
                    foundReplicas += 1
            # Update number of replicas
            if index > self._trial.replicas_per_thesis:
                self._trial.replicas_per_thesis = index
                self._trial.save()
        return foundReplicas

    def extractAssessmentData(self, columnName, evaluation,
                              assessmentSet):
        # Explore all the rows of this columns to extract data
        for index in range(1, self._numberRows):
            thesisInfo = self._table.loc[index, columnName]
            # Notice coincidence that index is the row in the table
            # and also the number of the thesis. It could be different
            # if the layout of the table is different
            replicas = self._replicaDict[index]
            values = thesisInfo.split('\r')
            replicaIndex = 1
            for value in values:
                # Remember the last item is the average value
                if replicaIndex in replicas:
                    self.saveDataPoint(
                        value, evaluation,
                        assessmentSet, replicas[replicaIndex])
                    replicaIndex += 1


# Class for tables with one line in header and values spread in rows
class AssmtTableSimpleHeader(AssmtTable):

    _indexReplicaColumn = None
    _replicasColumnName = None
    _firstRowValuesNames = None

    def __init__(self, table, trial, language=TrialTags.LANG_EN):
        super().__init__(table, trial, language=language)
        self._indexfirstColumnWithValues = None
        # there might be empty
        self.findColumnWithReplicaNames()
        # keep this order
        self.findFirstColumnValues()

    def isValid(self):
        if self._indexReplicaColumn is not None and\
           self._replicasColumnName is not None and\
           self._indexfirstColumnWithValues is not None and\
           self._firstRowValuesNames is not None:
            return True
        else:
            return False

    def findFirstColumnValues(self):
        if self._indexReplicaColumn is None or\
           self._firstRowValuesNames is None:
            return
        for index in range(self._indexReplicaColumn+1, self._numberColumns):
            # start from replicasColumn
            thisColumn = self._columns[index]
            value = self._table.loc[self._firstRowValuesNames, thisColumn]
            # We expect numbers
            if isinstance(value, str):
                valueFloat = self.convertToFloat(value)
                if valueFloat is not None:
                    self._indexfirstColumnWithValues = index
                    return

    def findColumnWithReplicaNames(self):
        foundPlot = False
        positionPlot = 0
        for index in range(0, self._numberColumns):
            columnName = self._table.columns[index]
            for indexRow in range(0, self._numberRows):
                value = self._table.loc[indexRow, columnName]
                if isinstance(value, str):
                    if (not foundPlot) and \
                       'Plot' in value or 'Parcela' in value:
                        foundPlot = True
                        positionPlot = indexRow
                        continue
                    if foundPlot and\
                       ('Mean' in value or 'Promedio' in value):
                        self._indexReplicaColumn = index
                        self._replicasColumnName = columnName
                        self._firstRowValuesNames = positionPlot + 1
                        return

    def findRowPosition(self, columnName, key):
        # Maybe the key is in the columnText
        if key in columnName:
            return -1
        for index in range(0, self._numberRows):
            values = self._table.loc[index, columnName]
            if isinstance(values, str) and key in values:
                return index
        return None

    def getValueAtRow(self, columnName, position):
        if position == -1:
            return columnName
        checkPosition = position - self._correctPosition
        return self._table.loc[checkPosition, columnName]

    def extractThesis(self):
        if self._firstColumnName == self._replicasColumnName:
            fReplicas, fThesis = self.extractThesisAndReplicaSameColumn()
        else:
            fReplicas, fThesis = self.extractThesisAndReplicaDifferentColumn()

        # Update number of replicas
        if fThesis > 0:
            number_replicas_thesis = fReplicas / fThesis
            if number_replicas_thesis > self._trial.replicas_per_thesis:
                self._trial.replicas_per_thesis = number_replicas_thesis
                self._trial.save()
        return fReplicas

    def extractThesisAndReplicaSameColumn(self):
        # Replica names are in same column as thesis but in different lines
        # expect for the first replica
        foundReplicas = 0
        lastThesis = None
        foundThesis = 0
        indexReplica = 1
        expectThesis = True

        for indexRow in range(self._firstRowValuesNames, self._numberRows):
            rowInfo = self._table.loc[indexRow, self._firstColumnName]
            if isinstance(rowInfo, str):
                # Lets make sure that there is data in this row, otherwise skip
                # For instance check last column. Like Botrybel FRESON 3
                # It may be that last column is empty (See
                #  20220701 BELTHIRUL 16 SC PIMIENTO MURCIA 01)
                foundData = False
                for indexColumn in range(2, self._numberColumns):
                    lastColumn = self._columns[indexColumn]
                    dataInfo = self._table.loc[indexRow, lastColumn]
                    if isinstance(dataInfo, str):
                        foundData = True
                        break
                if not foundData:
                    continue

                # Now, we believe there is data here
                if expectThesis:
                    if 'Mean' in rowInfo or 'Promedio' in rowInfo:
                        expectThesis = True
                        continue
                    number, thesisName, firstReplicaName = self.extractThesisInfo(rowInfo)
                    if thesisName is not None:
                        # Register Thesis
                        foundThesis += 1
                        if number is None:
                            number = foundThesis

                        lastThesis = self.findOrCreateThesis(
                            thesisName, number)

                        replica = self.findOrCreateReplica(
                                firstReplicaName,
                                1,
                                lastThesis)
                        if replica is not None:
                            self._replicaDict[indexRow] = replica
                            expectThesis = False
                            indexReplica = 2
                            foundReplicas += 1
                else:
                    if 'Mean' in rowInfo or 'Promedio' in rowInfo:
                        expectThesis = True
                        continue

                    replica = self.findOrCreateReplica(
                            rowInfo,
                            indexReplica,
                            lastThesis)
                    if replica is not None:
                        self._replicaDict[indexRow] = replica
                        indexReplica += 1
                        foundReplicas += 1

        return foundReplicas, foundThesis

    def extractThesisAndReplicaDifferentColumn(self):
        # We need the first column and the column with the replicas
        foundReplicas = 0
        lastThesis = None
        foundThesis = 0
        indexReplica = 1
        for indexRow in range(self._firstRowValuesNames, self._numberRows):
            thesisInfo = self._table.loc[indexRow, self._firstColumnName]
            if isinstance(thesisInfo, str):
                number, name, firstReplicaName = self.extractThesisInfo(thesisInfo)
                if name is not None:
                    # Register Thesis
                    foundThesis += 1
                    if number is None:
                        number = foundThesis
                    lastThesis = self.findOrCreateThesis(name, number)
                    indexReplica = 1
            # Register Replica. In the same row we should find the replica
            replicaInfo = self._table.loc[indexRow, self._replicasColumnName]
            # There could be a nan
            if not isinstance(replicaInfo, str):
                continue
            if 'Mean' in replicaInfo or 'Promedio' in replicaInfo:
                continue
            replica = self.findOrCreateReplica(
                    replicaInfo,
                    indexReplica,
                    lastThesis)
            if replica is not None:
                self._replicaDict[indexRow] = replica
                indexReplica += 1
                foundReplicas += 1
        return foundReplicas, foundThesis

    def extractAssessmentData(self, columnName, evaluation,
                              assessmentSet):
        # Explore all the rows of this columns to extract data
        for index in self._replicaDict:
            replica = self._replicaDict[index]
            value = self._table.loc[index, columnName]
            # Notice coincidence that index is the row in the table
            # and also the number of the thesis. It could be different
            # if the layout of the table is different
            self.saveDataPoint(
                        value, evaluation,
                        assessmentSet, replica)


class ImportPdfTrial:
    _filepath = None
    _tables = None
    _driver = None
    _thesis = None
    _products = None
    _evals = []
    _assessments = []
    _trial = None
    _importedTable = 0
    _debug = False

    def __init__(self, filename, debugInfo=False, language=TrialTags.LANG_EN):
        self._filepath = filename
        self._language = language
        self._debug = debugInfo
        self._evals = []
        self._trial = None
        self._importedTable = 0
        self._tables = tabula.read_pdf(
            filename, pages='all',
            lattice=False,
            multiple_tables=True)
        print('--------------------------------------')
        print(filename)
        print('Found {} tables'.format(len(self._tables)))

    def findKeyInColumnNames(self, table, key, index=0):
        return True if key in table.columns[index] else False

    def isKeyInTableColumns(self, table, key, index=0):
        return self.findKeyInColumnNames(table, key, index=index)

    def findInAllColumns(self, table, key):
        for column in table.columns:
            if key in column:
                return True
        return False

    def isProductThesisTable(self, table):
        return self.isKeyInTableColumns(table, 'Product')

    def isThesisTable(self, table):
        if self.isKeyInTableColumns(table, 'Trt') and\
           self.findInAllColumns(table, 'Product'):
            return True
        return False

    def isKeyInTableRows(self, table, key, column):
        index = 0
        lenghtTable = len(table)
        for index in range(0, lenghtTable):
            value = table.loc[index, column]
            if isinstance(value, str):
                if key in value:
                    return True
        return False

    def isValuesTable(self, table):
        # There are 2 observed views:
        # if the header contains multiple lines
        self.printTable(table)
        leftTopHeader = table.columns[0]
        multiLine = None
        foundKeys = []
        if len(leftTopHeader.split('\r')) == 1:
            multiLine = False
            for key in TrialTags.getKeyTags(self._language):
                if self.isKeyInTableRows(table, key, leftTopHeader):
                    foundKeys.append(key)        
        else:
            multiLine = True
            for key in TrialTags.getKeyTags(self._language):
                if self.isKeyInTableColumns(table, key):
                    foundKeys.append(key)
        compareSets = [TrialTags.TAG_TYPES, TrialTags.TAG_DATES]
        for aSet in compareSets:
            found = False
            for key in aSet:
                if key in foundKeys:
                    found = True
                    break
            if not found:
                return None
        if multiLine:
            return AssmtTableMultiLineHeader
        else:
            return AssmtTableSimpleHeader

    def printTable(self, table):
        if self._debug:
            print(table.to_markdown())

    def log(self, msg):
        if self._debug:
            print(msg)

    def isAssessmentTable(self, table):
        return self.isKeyInTableColumns(table, 'Assessment\rdate')

    def walkThrough(self):
        evals = []
        for table in self._tables:
            # if self.isThesisTable(table):
            #     self._thesis = table
            #     self.log('>>> thesis table')
            #     continue
            # if self.isProductThesisTable(table):
            #     self._products = table
            #     self.log('>>> product table')
            #     continue
            # if self.isAssessmentTable(table):
            #     self._assessments = table
            #     self.log('>>> assessment table')
            #     continue
            classTable = self.isValuesTable(table)
            if classTable:
                evals.append([classTable, table])
        if len(evals) == 0:
            return False

        self.createTrial()
        for eval in evals:
            evalTable = eval[0](eval[1], self._trial, language=self._language)
            if evalTable.isValid():
                self._evals.append(evalTable)
        return True

    def getCode(self, filename):
        return filename.split(' ')[0]

    def getProduct(self, filename):
        productName = filename.split(' ')[1]
        products = Product.objects.filter(name__iexact=productName)
        if not products:
            return Product.getUnknown()
        else:
            return products[0]

    def getFilename(self):
        return self._filepath.split('/')[-1].split('.')[0]

    def createTrial(self):
        name = self.getFilename()
        code = self.getCode(name)
        if FieldTrial.objects.filter(code=code).exists():
            self._trial = FieldTrial.objects.get(code=code)
        else:
            self._trial = FieldTrial.objects.create(
                name=name,
                objective=Objective.getUnknown(),
                responsible='BaaS Imported',
                project=Project.getUnknown(),
                product=self.getProduct(name),
                crop=Crop.getUnknown(),
                plague=Plague.getUnknown(),
                blocks=4,
                replicas_per_thesis=0,
                trial_status=TrialStatus.objects.get(name='Imported'),
                # report_filepath=self._filepath,
                trial_type=TrialType.getUnkown(),
                code=code)

    def run(self):
        if not self.walkThrough():
            return
        for table in self._evals:
            self.printTable(table._table)
            if table.extractTableData():
                table.cleanUp()
                self._importedTable += 1
        print('Imported tables {}/{}'.format(
            self._importedTable,
            len(self._evals)))
        return


def importOneOld():
    """Run administrative tasks."""
    # os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'baaswebapp.dev')
    path = '/Users/jsantiago/Documents/estudios/botrybel/to be imported/'
    # fileName = path + '20150201 BOTRYBEL EFICACIA FRESÓN 01.pdf'
    # fileName = path+'20171102 BOTRYBEL EFICACIA CPCP PEPINO PORTUGAL 09.pdf'
    # fileName = path+'20110202 BOTRYBEL EFICACIA FRESÓN 02.pdf'
    # fileName = path+'20110408 BOTRYBEL EFICACIA FRESÓN 03.pdf'
    # fileName = path+'20110302 BOTRYBEL EFICACIA CEBOLLA 04.pdf'
    # fileName = path+'20170501 BOTRYBEL EFICACIA FRESÓN 09.pdf'
    # fileName = path+'20170405 BOTRYBEL EFICACIA FRESÓN 10.pdf'
    # fileName = path+'20170329 BOTRYBEL EFICACIA FRESÓN 11.pdf'
    path = '/Users/jsantiago/Library/CloudStorage/OneDrive-PROBELTE,SAU/Data/estudios/toimport/'
    # fileName = path + '20220903 INFORME FINAL  PowerEkky WP Lechuga  BAAS.pdf'
    fileName = path + '20220905 INFORME FINAL  SoilEkky WP Lechuga  BAAS.pdf'
    importer = ImportPdfTrial(fileName, debugInfo=True,
                              language=TrialTags.LANG_ES)
    importer.run()

    fileName = path + '20220906 INFORME FINAL  SoilEkky WP Brocoli BAAS.pdf'
    importer = ImportPdfTrial(fileName, debugInfo=True,
                              language=TrialTags.LANG_ES)
    importer.run()


def importOne():
    path = '/Users/jsantiago/Library/CloudStorage/OneDrive-PROBELTE,SAU/Data/estudios/2022/'
    fileName = path + '20220303 BOTRYBEL (PB050 Y PB051) PATATA ALTERNARIA MURCIA.pdf'
    importer = ImportPdfTrial(fileName, debugInfo=True,
                              language=TrialTags.LANG_EN)
    importer.run()


def importReport(
        filename,
        path='/Users/jsantiago/Documents/estudios/botrybel/to be imported/'):
    fileNamePath = path+filename
    importer = ImportPdfTrial(fileNamePath, debugInfo=True)
    importer.run()


def importAll():
    inDir = '/Users/jsantiago/Library/CloudStorage/OneDrive-PROBELTE,SAU/Data/estudios/2022'
    for root, dirs, files in os.walk(os.path.realpath(inDir)):
        for filename in files:
            filepath = root+'/'+str(filename)
            try:
                importer = ImportPdfTrial(filepath, debugInfo=True)
                importer.run()
            except Exception:
                print("[EEE]{}".format(filename))


def discoverReport(inDir, outDir, productos):
    for root, dirs, files in os.walk(os.path.realpath(inDir)):
        print('\r {}'.format(root), end='')
        for filename in files:
            try:
                foundProduct = False
                for key in productos:
                    if key in filename:
                        foundProduct = True
                if foundProduct and '20' == filename[:2] and\
                   filename[-4:] in ['.pdf', '.doc']:
                    origin = root+'/'+str(filename)
                    outFile = outDir+'/'+str(filename)
                    shutil.copy2(origin, outFile)
                    print('> {}'.format(filename))
                else:
                    pass
            except Exception:
                print("[EEE]{}".format(filename))


def discoverReports():
    inDir = '/Volumes/marketing/EXTERNO BMOVE/ENSAYOS FUN BIOLOGICOS/'
    # inDir = '/Volumes/marketing/EXTERNO BMOVE/'
    # outDir = '/Users/jsantiago/Documents/estudios/belthirul'
    outDir = '/Users/jsantiago/Documents/estudios/discovered'
    products = ['BOTRYBEL', 'PB001', 'PB050']
    discoverReport(inDir, outDir, products)


if __name__ == '__main__':
    importOne()
    # discoverReports()
    # importAll()
