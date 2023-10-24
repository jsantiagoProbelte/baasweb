import os
import django
import tabula
from dateutil.relativedelta import relativedelta
from dateutil.parser import parse
import shutil
import numpy as np
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'baaswebapp.dev')
django.setup()
from baaswebapp.baas_archive import BaaSArchive  # noqa: E402
from baaswebapp.models import Weather  # noqa: E402
from baaswebapp.models import ModelHelpers, RateTypeUnit  # noqa: E402
from trialapp.models import FieldTrial, Crop, Objective, Plague, \
    Thesis, Replica, StatusTrial, TrialType, TreatmentThesis, \
    Application, PartRated, Sample  # noqa: E402
from trialapp.data_models import ReplicaData, Assessment, \
    SampleData  # noqa: E402
from catalogue.models import Product, Treatment, \
    UNTREATED, DEFAULT, RateUnit, Vendor  # noqa: E402
from trialapp.trial_helper import TrialFile, PdfTrial  # noqa: E402
import glob  # noqa: E402
import csv  # noqa: E402
from trialapp.trial_analytics import Abbott  # noqa: E402


class TrialTags:
    RATING_UNIT = 'Rating Unit'
    ASSESSMENT_UNIT = 'Assessment Unit'  # Assessment Unit/Min/Max
    RATING_UNIT_ES = 'Rating Unit'
    TAG_UNITS = [RATING_UNIT, ASSESSMENT_UNIT, RATING_UNIT_ES]

    CROP_STAGE_ES = 'Estado del cultivo Mayoritario/Min/Max'
    CROP_STAGE = 'Crop Stage Majority'
    TAG_STAGES = [CROP_STAGE, CROP_STAGE_ES, 'rop Stage Majority/Min/Max',
                  'BBCH Code']

    INTERVAL_ES = 'Trt-Eval Interval'
    INTERVAL = 'Trt-Eval Interval'
    TAG_INTERVALS = [INTERVAL, INTERVAL_ES, 'rt-Eval Interval']

    RATING_TYPE = 'Rating Type'
    ASSESSMENT_TYPE = 'Assessment Type'
    RATING_TYPE_ES = 'Descripción'
    TAG_TYPES = [ASSESSMENT_TYPE, RATING_TYPE, RATING_TYPE_ES, 'ating Type',
                 'Rating T ype']

    RATING_DATE = 'Rating Date'
    RATING_DATE_ES = 'Fecha Valoración'
    ASSESSMENT_DATE = 'Assessment Date'
    TAG_DATES = [RATING_DATE, ASSESSMENT_DATE, RATING_DATE_ES, 'ating Date']

    PEST_CODE = 'Pest Code'
    PEST_CODE_ES = 'Código Plaga'
    TAG_PESTS = [PEST_CODE, PEST_CODE_ES, 'est Code']

    CROP_CODE = 'Crop Code'
    CROP_CODE_ES = 'Código cultivo'
    CROP_NAME = 'Crop Name'
    TAG_CROPS = [CROP_CODE, CROP_NAME, CROP_CODE_ES, 'rop Type, Code']

    SAMPLING_SIZE = 'Sample Size'
    SAMPLING_SIZE_ES = 'Numero submuestras'
    TAG_SIZE = [SAMPLING_SIZE, SAMPLING_SIZE_ES, 'ample Size']

    PART_ASSESSED = 'Part Assessed'
    PART_RATED = 'Part Rated'
    TAG_PARTS = [PART_ASSESSED, PART_RATED]

    KEY_TAGS = [TAG_DATES, TAG_TYPES]
    ALL_TAGS = [TAG_UNITS, TAG_STAGES, TAG_TYPES, TAG_DATES, TAG_PESTS,
                TAG_PESTS, TAG_CROPS, TAG_SIZE, TAG_INTERVALS, TAG_PARTS]

    TAG_MEANS = ['Mean', 'Promedio']

    CROPS = {'CUMSA': 'cucumber', 'FRASS': 'Strawberry', 'PRNPS': 'Peach',
             'Strawberry': 'Strawberry',
             'LACSA': 'Lettuce', 'C; LACSA': 'Lettuce', 'ALLAM': 'Garlic',
             'BRSOL': 'Wild Cabbage', 'C; BRSOK': 'Brocoli',
             'LYPES': 'Tomato', 'FRAS': 'Strawberry',
             'CPSAN': 'Bell Pepper', 'C; TRZDS': "Durum Wheat",
             'MABSD': 'Apple', 'RUBID': 'Red Raspberry',
             'VACCO': 'Blueberry', 'BRSOB': 'Cauliflower',
             'ATICH': 'Kiwi', 'CIDCL': '',
             'C; VITVI': 'Grape', 'VITVI': 'Grape', 'ALLCE': "Onion"}
    PESTS = {'BOTRCI': 'botrytis', 'MONIFG': 'Moniliosis',
             'PUCCSP': 'Wheat yellow rust', 'CARPPO': 'Codling moth',
             'BOTRSP': 'botrytis', 'HELIAR': 'Helicoverpa armigera',
             'ARGTSP': 'Moth - Argyrotaenia ljungiana'}

    TRAILERS = ['ABCDEFHIJKLM', 'HIJKLM', 'IJKLMN', 'BCDEFG', 'ABCDEF', 'ABCD',
                'CDEFGHJKLMNO', 'CDEFGH', 'JKLMNO']

    @classmethod
    def isMeanTag(cls, value):
        for tag in TrialTags.TAG_MEANS:
            if tag in value:
                return True
        return False


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

    def __init__(self, table):
        self._table = table
        self._firstRowValuesNames = 1
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

    def prepareThesis(self):
        for thesis in Thesis.getObjects(self._trial):
            joinName = thesis.name.replace(" ", "")
            self._thesis[joinName] = thesis

    def findOrCreateThesis(self, name, number):
        thesis = self.existThesisByNumber(number)
        if thesis is None:
            thesis = self.existThesis(name)
        if thesis is None or thesis.number != number:
            thesis = Thesis.findOrCreate(
                            name=name.strip(),
                            number=number,
                            field_trial=self._trial)
        return thesis

    def findOrCreateReplica(self, name, number, thesis):
        name = self.replaceApplicationTrailers(name)
        if name.isdigit() and len(name) < 4:
            nameReplica = f'{int(name):03}'
            return Replica.findOrCreate(
                            name=nameReplica,
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

    def existThesisByNumber(self, number):
        for thesisName in self._thesis:
            thesis = self._thesis[thesisName]
            if number == thesis.number:

                return thesis
        return None

    def isStatisticalTable(self):
        tokens = ['Standard Deviation', 'Bartlett', 'Tukey']
        for index in range(0, 3):
            columnName = self._table.columns[index]
            for indexRow in range(0, self._numberRows):
                value = self._table.loc[indexRow, columnName]
                if isinstance(value, str):
                    for token in tokens:
                        if token in value:
                            return True
        return False

    def isValid(self):
        if self._indexfirstColumnWithValues is not None:
            # Do we have replicas or is just a summary table
            if self.isStatisticalTable():
                return False
            return True
        else:
            return False

    def getValueAtRow(self, values, position):
        raise PdfImportExport_using_based_class()

    def findRowPosition(self, columnText, key):
        raise PdfImportExport_using_based_class()

    def getKeyTrialValues(self, model, tagSet, valuesDict):
        # Lets check in which row shows 'Crop Code'
        keyColumnValues = self._columns[self._indexfirstColumnWithValues]
        value = self.getTagPositionValue(keyColumnValues, tagSet, None)

        if value:
            if value in valuesDict:
                return model.objects.get(name__iexact=valuesDict[value])
            else:
                return model.findOrCreate(name=value)
        return None

    def getPest(self):
        if self._trial.plague.name != ModelHelpers.UNKNOWN:
            return
        result = self.getKeyTrialValues(
            Plague, TrialTags.TAG_PESTS, TrialTags.PESTS)
        if result:
            self._trial.plague = result
            self._trial.save()

    def getCrop(self):
        if self._trial.crop.name != ModelHelpers.UNKNOWN:
            return
        result = self.getKeyTrialValues(
            Crop, TrialTags.TAG_CROPS, TrialTags.CROPS)
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
        if len(thesisInfo) > 10 and thesisInfo[-3:].isdigit():
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
        name = self.replaceApplicationTrailers(thesisInfo)
        return number, name, firstReplica

    def getTagPositionValue(self, columnName, tagSet, default):
        position = None
        for tag in tagSet:
            if tag in self._tagPositions:
                position = self._tagPositions.get(tag, None)
        if position is None:
            return default
        return self.getValueAtRow(columnName, position)

    def findTagPositions(self):
        for tagSet in TrialTags.ALL_TAGS:
            for tag in tagSet:
                position = self.findRowPosition(self._firstColumnName, tag)
                if position is not None:
                    self._tagPositions[tag] = position
                    break
        return

    def extractEvaluations(self):
        # Get some useful positions of tags
        for columnIndex in range(self._indexfirstColumnWithValues,
                                 self._numberColumns):
            columnName = self._columns[columnIndex]
            rateType = self.extractRateTypeInfo(columnName)
            assessment = self.extractAssessmentInfo(columnName, rateType)
            if assessment is None:
                # Abort
                continue
            self.extractAssessmentData(columnName, assessment)

    def getValidDate(self, dateStr):
        # check if this is date
        try:
            if not isinstance(dateStr, str) or len(dateStr) < 6:
                return None
            return None if dateStr is None else parse(dateStr, fuzzy=False)
        except ValueError:
            return None

    def correctDatePosition(self, columnName):
        positionDate = None
        for tag in TrialTags.TAG_DATES:
            if tag in self._tagPositions:
                positionDate = self._tagPositions.get(tag, None)
                break
        for i in range(-3, 4):
            newPosition = positionDate - i
            if newPosition < 1:
                # if newPosition is bigger than posible it will handle
                # by getValueAtRow
                continue
            theDateStr = self.getValueAtRow(columnName, newPosition)
            theDate = self.getValidDate(theDateStr)
            if theDate:
                self._correctPosition = i
                return theDate
        # we failed to find a date
        print('>>>>> Cannot find date')
        return None

    def getRatingDate(self, columnName):
        # we reset this correction, in the first value query per column
        # which is for date, because it is also the easier to identify
        # if we get it wrong
        self._correctPosition = 0
        theDateStr = None

        theDateStr = self.getTagPositionValue(
            columnName, TrialTags.TAG_DATES, None)

        theDate = self.getValidDate(theDateStr)
        if theDate:
            return theDate
        return self.correctDatePosition(columnName)

    def getCropStage(self, columnName):
        bbch = self.getTagPositionValue(
            columnName, TrialTags.TAG_STAGES, ModelHelpers.UNDEFINED)
        if bbch is None:
            bbch = ModelHelpers.UNDEFINED
        return bbch

    def getPartRated(self, columnName):
        return self.getTagPositionValue(
            columnName, TrialTags.TAG_PARTS, ModelHelpers.UNDEFINED)

    def isColumnWithValues(self, columnName):
        value1 = self._table.loc[self._firstRowValuesNames, columnName]
        value2 = self._table.loc[self._firstRowValuesNames+1, columnName]
        if isinstance(value1, str) and isinstance(value2, str):
            return True
        return False

    def extractAssessmentInfo(self, columnName, rateType):
        # Validate that we have values in these column
        if not self.isColumnWithValues(columnName):
            print('>>>>> Cannot find assessment')
            return None

        # Each assessment is in a different column
        theDate = self.getRatingDate(columnName)
        if theDate is None:
            # Abort
            print('>>>>> Cannot find assessment date')
            return None

        stage = self.getCropStage(columnName)

        part_rated = self.getPartRated(columnName)

        interval = self.getTagPositionValue(
            columnName, TrialTags.TAG_INTERVALS, 'Unknown')
        if not interval:
            interval = "{}-({})".format(theDate, stage)

        return Assessment.findOrCreate(
                name=interval,
                assessment_date=theDate,
                field_trial=self._trial,
                part_rated=part_rated,
                rate_type=rateType,
                crop_stage_majority=stage)

    def extractRateTypeInfo(self, columnName):
        # Each column may have different assessment type and units
        typeName = self.getTagPositionValue(
            columnName, TrialTags.TAG_TYPES, ModelHelpers.UNKNOWN)
        unitName = self.getTagPositionValue(
            columnName, TrialTags.TAG_UNITS, ModelHelpers.UNKNOWN)
        rate_type = RateTypeUnit.findOrCreate(name=typeName, unit=unitName)

        return rate_type

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

    def saveDataPoint(self, value, assessment, replica):
        valueFloat = self.convertToFloat(value)
        if valueFloat is not None:
            ReplicaData.findOrCreate(
                value=self.convertToFloat(valueFloat),
                assessment=assessment,
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

    def replaceApplicationTrailers(self, name):
        for trailer in TrialTags.TRAILERS:
            if trailer in name:
                name = name.replace(trailer, '')
        return name.strip()


# Class for tables with multiple lines inside the header
class AssmtTableMultiLineHeader(AssmtTable):

    def __init__(self, table):
        super().__init__(table)

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
            if index > self._trial.repetitions:
                self._trial.repetitions = index
                self._trial.save()
        return foundReplicas

    def extractAssessmentData(self, columnName, assessment):
        # Explore all the rows of this columns to extract data
        thesisList = list(self._replicaDict.keys())
        for index in range(1, self._numberRows):
            thesisInfo = self._table.loc[index, columnName]
            # Notice coincidence that index is the row in the table
            # and also the number of the thesis. It could be different
            # if the layout of the table is different
            # ... thesisList should solve this, by checking the
            thesisPosition = thesisList[index-1]
            replicas = self._replicaDict[thesisPosition]
            values = thesisInfo.split('\r')
            replicaIndex = 1
            for value in values:
                # Remember the last item is the average value
                if replicaIndex in replicas:
                    self.saveDataPoint(
                        value, assessment, replicas[replicaIndex])
                    replicaIndex += 1


# Class for tables with one line in header and values spread in rows
class AssmtTableSimpleHeader(AssmtTable):

    _indexReplicaColumn = None
    _replicasColumnName = None
    _firstRowValuesNames = None

    def __init__(self, table):
        super().__init__(table)
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
                        # Let's assume this is column for replicas
                        self._firstRowValuesNames = positionPlot + 1
                        self._replicasColumnName = columnName
                        self._indexReplicaColumn = index
                        # unless we found "mean" in another columns
                        continue
                    if foundPlot and TrialTags.isMeanTag(value):
                        self._replicasColumnName = columnName
                        self._indexReplicaColumn = index
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
            if number_replicas_thesis > self._trial.repetitions:
                self._trial.repetitions = number_replicas_thesis
                self._trial.save()
        return fReplicas

    def foundData(self, indexRow):
        for indexColumn in range(2, self._numberColumns):
            lastColumn = self._columns[indexColumn]
            dataInfo = self._table.loc[indexRow, lastColumn]
            if isinstance(dataInfo, str):
                return True
        return False

    def makeReplica(self, replicaName, replicaNumber, replicaPosition, thesis):
        replica = self.findOrCreateReplica(replicaName, replicaNumber, thesis)
        if replica is not None:
            self._replicaDict[replicaPosition] = replica
            return True
        else:
            return False

    def extractThesisAndReplicaSameColumn(self):
        # Replica names are in same column as thesis but in different lines
        # expect for the first replica
        foundReplicas = 0
        lastThesis = None
        foundThesis = 0
        indexReplica = 1
        expectThesis = True
        replicaName = None

        for indexRow in range(self._firstRowValuesNames, self._numberRows):
            rowInfo = self._table.loc[indexRow, self._firstColumnName]
            if isinstance(rowInfo, str):
                # Lets make sure that there is data in this row, otherwise skip
                # For instance check last column. Like Botrybel FRESON 3
                # It may be that last column is empty (See
                #  20220701 BELTHIRUL 16 SC PIMIENTO MURCIA 01)
                if not self.foundData(indexRow):
                    continue

                # Now, we believe there is data here
                if expectThesis:
                    if TrialTags.isMeanTag(rowInfo):
                        expectThesis = True
                        continue
                    nmb, tN, replicaName = self.extractThesisInfo(rowInfo)
                    if tN is not None:  # thesisName
                        # Register Thesis
                        if nmb is None:
                            nmb = foundThesis
                        lastThesis = self.findOrCreateThesis(tN, nmb)
                        expectThesis = False
                        foundThesis += 1
                        indexReplica = 1
                    else:
                        continue
                else:
                    if TrialTags.isMeanTag(rowInfo):
                        expectThesis = True
                        continue
                    replicaName = rowInfo
                if self.makeReplica(replicaName, indexReplica, indexRow,
                                    lastThesis):
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
                number, name, fRN = self.extractThesisInfo(thesisInfo)
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
            if TrialTags.isMeanTag(replicaInfo):
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

    def extractAssessmentData(self, columnName, assessment):
        # Explore all the rows of this columns to extract data
        for index in self._replicaDict:
            replica = self._replicaDict[index]
            value = self._table.loc[index, columnName]
            # Notice coincidence that index is the row in the table
            # and also the number of the thesis. It could be different
            # if the layout of the table is different
            self.saveDataPoint(value, assessment, replica)


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

    def __init__(self, filename, debugInfo=False):
        self._filepath = filename
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

    def isTreatmentTable(self, table):
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
        leftTopHeader = table.columns[0]
        multiLine = False if len(leftTopHeader.split('\r')) == 1 else True

        for keySet in TrialTags.KEY_TAGS:
            found = False
            for key in keySet:
                if multiLine:
                    found = self.isKeyInTableColumns(table, key)
                else:
                    found = self.isKeyInTableRows(table, key, leftTopHeader)
                if found:
                    break
            if not found:
                print('>>>> Not Found Keys')
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
        indexTable = 1
        for table in self._tables:
            print('------->>>({})<<<<------------'.format(indexTable))
            self.printTable(table)
            # if self.isThesisTable(table):
            #     self._thesis = table
            #     self.log('>>> thesis table')
            #     continue
            # if self.isTratementTable(table):
            #     self._products = table
            #     self.log('>>> product table')
            #     continue
            # if self.isAssessmentTable(table):
            #     self._assessments = table
            #     self.log('>>> assessment table')
            #     continue
            classTable = self.isValuesTable(table)
            if classTable:
                evalTable = classTable(table)
                # DEBUG
                if evalTable.isValid():
                    self._evals.append(evalTable)
                else:
                    print('>>>>> No replicas found')
            indexTable += 1

        if len(self._evals) == 0:
            return False
        self.createTrial()
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
                product=self.getProduct(name),
                crop=Crop.getUnknown(),
                plague=Plague.getUnknown(),
                repetitions=4,
                status_trial=StatusTrial.REWIEW,
                trial_type=TrialType.getUnknown(),
                code=code)
        for evalTable in self._evals:
            evalTable._trial = self._trial

    def run(self):
        if not self.walkThrough():
            return False
        print(".......................................")
        for table in self._evals:
            self.printTable(table._table)
            if table.extractTableData():
                table.cleanUp()
                self._importedTable += 1
        print('Imported tables {}/{}'.format(
            self._importedTable,
            len(self._evals)))
        if self._importedTable > 0:
            TrialFile().uploadTrialFile(self._trial,
                                        self._filepath)
            return True
        else:
            self._trial.delete()
            return False


untreated = Treatment.objects.get(name=UNTREATED)
defaultRateUnit = RateUnit.objects.get(name=DEFAULT)
rateUnits = {unit.name: unit for unit in RateUnit.objects.all()}


def importThesis(thesis, scanInit, product):
    thesisName = thesis.name
    product = thesis.field_trial.product

    nameVariant = thesisName[0:scanInit]
    if thesisName[scanInit] in ['A', 'B', 'C' 'D', 'E', 'F', 'G']:
        nameVariant += thesisName[scanInit]
        scanInit += 1

    if thesisName[scanInit] != ' ':
        thesisName = thesisName[0:scanInit]+' '+thesisName[scanInit:-1]
        thesis.name = thesisName
        thesis.save()

    # let's find the dosis
    dosis = ''
    for index in range(scanInit+1, len(thesisName)):
        chart = thesisName[index]
        if chart.isdigit():
            dosis += chart
        elif chart in ['.', ',']:
            dosis += '.'
        elif chart == ' ':
            index += 1
            break
        else:
            break

    # let's find the unit, let's assume the rest of the name
    # is the unit
    unitStr = thesisName[index:]

    theRateUnit = defaultRateUnit
    if len(unitStr) > 1:
        theRateUnit = rateUnits.get(unitStr, None)
        if theRateUnit is None:
            theRateUnit = RateUnit.findOrCreate(name=unitStr)
            rateUnits[unitStr] = theRateUnit

    # let's create the treatment
    treatment = Treatment.findOrCreate(product=product,
                                       rate=dosis,
                                       rate_unit=theRateUnit)
    TreatmentThesis.findOrCreate(thesis=thesis,
                                 treatment=treatment)
    print('>>>>[Created] {}\n{}\t{}\t'.format(
        product.name,
        unitStr,
        treatment.rate))
    return True


def createThesisTreatments():
    total = 0
    withTreatments = 0
    created = 0

    for thesis in Thesis.objects.all():
        total += 1
        treatments = TreatmentThesis.objects.filter(thesis=thesis)
        if treatments:
            withTreatments += 1
            continue

        if 'Untreat' in thesis.name:
            TreatmentThesis.objects.create(treatment=untreated,
                                           thesis=thesis)
            continue

        thesisName = thesis.name
        if thesisName == 'PB001 8mL/L':
            print('lo encontre')

        print('\r[{}]{}'.format(thesis.id, thesisName))

        toImport = False
        if thesisName[:2] == 'PB' and thesisName[2:5].isdigit() and\
           len(thesisName) > 10:
            toImport = True
            # This is a PBXXX product.
            # Let's added as a formulation
            scanInit = 5
        elif 'Serenade' in thesisName or 'SERENADE' in thesisName:
            toImport = True
            scanInit = 8

        if toImport:
            if importThesis(thesis, scanInit):
                created += 1

    print("Scan {}, with treatment{}, created {}".format(
        total, withTreatments, created))


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
    path = '/Users/jsantiago/Library/CloudStorage/OneDrive-PROBELTE,SAU/Data/'\
           'estudios/toimport/'
    # fileName = path + '20220903 INFORME FINAL  PowerEkky WP Lechuga
    # BAAS.pdf'
    fileName = path + '20220905 INFORME FINAL  SoilEkky WP Lechuga  BAAS.pdf'
    importer = ImportPdfTrial(fileName, debugInfo=True)
    importer.run()

    fileName = path + '20220906 INFORME FINAL  SoilEkky WP Brocoli BAAS.pdf'
    importer = ImportPdfTrial(fileName, debugInfo=True)
    importer.run()


def importOneMapa():
    path = '/Users/jsantiago/Library/CloudStorage/OneDrive-PROBELTE,SAU/Teams'\
           '/General/Iniciativas/SIEX/'
    fileName = path + '15d0019c-663f-4147-9a9c-eca7a729a741.pdf'
    importer = ImportPdfTrial(fileName, debugInfo=True)
    importer.run()


def importReport(
        filename,
        path='/Users/jsantiago/Documents/estudios/botrybel/to be imported/'):
    fileNamePath = path+filename
    importer = ImportPdfTrial(fileNamePath, debugInfo=True)
    importer.run()


def importAll():
    inDir = '/Users/jsantiago/Library/CloudStorage/OneDrive-PROBELTE,SAU/Data'\
            '/estudios/todo/belthirul/'
    moveDir = '/Users/jsantiago/Library/CloudStorage/OneDrive-PROBELTE,SAU/'\
              'Data/estudios/imported/'
    for root, dirs, files in os.walk(os.path.realpath(inDir)):
        for filename in files:
            move = False
            filepath = root+'/'+str(filename)
            nameTrial = filename.split('.')[0]
            if FieldTrial.objects.filter(name=nameTrial).exists():
                move = True
            else:
                try:
                    importer = ImportPdfTrial(filepath, debugInfo=True)
                    move = importer.run()
                except Exception:
                    print("[EEE]{}".format(filename))
            if move and moveDir:
                target = moveDir + str(filename)
                shutil.move(filepath, target)


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


def importOne():
    path = '/Users/jsantiago/Library/CloudStorage/OneDrive-PROBELTE,SAU/Data'\
           '/estudios/todo/'  # atlantis/'  # '/impello/'
    # '/estudios/todo/botrybel/'

    # fileName = path + '20221233 MDJ Elicitor Hemp Botrytis_22_Site''
    # ' Description - Standard Form_Dec-5-2022.pdf'
    # fileName = path + '20221215 MDJ Elicitor VITVI_CA_22_Site Description - '
    # 'Standard Form_Sep-15-2022.pdf'
    # fileName = path + '20230502 BOTRYBEL STRAWBERRY atlantis.pdf'
    # fileName = path + '20160902 BOTRYBEL EFICACIA ITALIA TOMATE 05 copia.pdf'
    fileName = path + '20220233 PB050, PB051, PB012, PB012B lettuce ' \
        'Sclerotinia sclerotiorum.pdf'
    # fileName = path + '20221102 P003 TOMATE.pdf'
    # fileName = path + '20220303 Informe Final Botrybel patata alternaria y '
    # 'mildiu.pdf'
    importer = ImportPdfTrial(fileName, debugInfo=True)
    importer.run()


def testArchive():
    archive = BaaSArchive()
    # archive.createFolder('20230101')
    archive.uploadFile('submit.sh', '/Users/jsantiago/Code/baasweb', 'prueba/')
    archive.downloadFile('submit.sh', 'prueba/', '/Users/jsantiago/Code/tmp')


def createTeams():
    helper = TrialFile()
    reference = '/Users/jsantiago/Library/CloudStorage/OneDrive-PROBELTE,SAU/'\
                'Data/estudios/imported/'

    for trial in FieldTrial.objects.all():
        print('{}>>'.format(trial.code))
        helper.createTrialFolder(trial.code)
        pattern = '*{}*.[pP][dD][fF]'.format(trial.code)
        filePattern = ''.join([reference, pattern])
        files = glob.glob(filePattern)
        for filepath in files:
            print('>>{}'.format(filepath))
            helper.uploadTrialFile(trial, filepath)


def exportPdf():
    trial = FieldTrial.objects.get(code='20160902')
    export = PdfTrial(trial)
    export.produce()


def createThesisReplicas(trialNumber):
    trial = FieldTrial.objects.get(code=trialNumber)
    fileName = '/Users/jsantiago/Code/dumps/treatments.csv'
    theses = {item.name: item for item in
              Thesis.getObjects(trial)}
    replicas = {item.name: item for item in
                Replica.getFieldTrialObjects(trial)}
    number = len(theses.keys()) + 1
    with open(fileName) as csvfile:
        reader = csv.DictReader(csvfile, delimiter=';')
        for row in reader:
            thesisName = row['\ufeffTreatment']
            if thesisName not in theses:
                thesis = Thesis.objects.create(name=thesisName,
                                               field_trial=trial,
                                               number=number)
                number += 1
                theses[thesisName] = thesis
            else:
                thesis = theses[thesisName]
            plot = row['Plot']
            if plot not in replicas:
                counts = Replica.objects.filter(thesis=thesis).count()
                Replica.objects.create(name=plot, number=counts+1,
                                       thesis=thesis)


def importConcreateCSV():
    trialNumber = '20230406'
    # fileName = '/Users/jsantiago/Code/dumps/Disease Severity Data.csv'
    fileName = '/Users/jsantiago/Code/dumps/incidencia.csv'
    dates = {'Harvest 1': '2023-03-28',
             'Harvest 2': '2023-04-04',
             'Harvest 3': '2023-04-11',
             'Harvest 4': '2023-04-18',
             'Harvest 5': '2023-04-25',
             'Harvest 6': '2023-05-02',
             'Harvest 7': '2023-05-09',
             'Harvest 8': '2023-05-16'}
    # createThesisReplicas(trialNumber)
    # rateType = RateTypeUnit.objects.filter(name='PESSEV', unit='%, 0, 100')
    rateType = RateTypeUnit.objects.filter(name='PESINC', unit='NUMBER')
    importCSV(trialNumber, fileName, rateType[0], 'FRUIT P', dates)


def importCSV(trialNumber, fileName, rateType, partRated, dates):
    trial = FieldTrial.objects.get(code=trialNumber)
    replicas = {replica.name: replica for replica in
                Replica.getFieldTrialObjects(trial)}

    with open(fileName) as csvfile:
        reader = csv.DictReader(csvfile, delimiter=';')
        header = reader.fieldnames

        assessments = {}
        for column in header:
            if column == '\ufeffPlot Number':
                continue
            assessments[column] = Assessment.findOrCreate(
                name=column,
                assessment_date=dates[column],
                part_rated=partRated,
                field_trial=trial,
                crop_stage_majority=ModelHelpers.UNDEFINED,
                rate_type=rateType)

        for row in reader:
            plot = row['\ufeffPlot Number']
            # Create replica if need it
            for column in header:
                if column == '\ufeffPlot Number':
                    continue
                value = row[column]
                value = value.replace(',', '.')
                valueF = float(value)

                ReplicaData.objects.create(
                    reference=replicas[plot],
                    assessment=assessments[column],
                    value=valueF)


def cleanPlagues():
    for plague in Plague.objects.all():
        tt = FieldTrial.objects.filter(plague=plague).count()
        if tt == 0:
            plague.delete()
        else:
            if plague.scientific is not None:
                plague.name = plague.scientific
                plague.save()


def exportCsvFile(filename, data):
    with open(filename, 'w', newline='') as csvfile:
        writer = csv.DictWriter(csvfile, delimiter=';',
                                fieldnames=list(data[0].keys()))
        writer.writeheader()
        # Write the data
        for row in data:
            writer.writerow(row)


def extractData():
    trialFields = [
        'id', 'irrigation', 'mode', 'soil', 'cultivation',
        'application_volume', 'avg_temperature', 'avg_humidity',
        'avg_precipitation', 'latitude', 'longitude']

    trials = FieldTrial.objects.filter(
        plague=Plague.objects.get(other='Botrytis'),
        crop=Crop.objects.get(name='Strawberry')).values(*trialFields)
    trialIds = [item['id'] for item in trials]

    exportCsvFile('./trials_data', trials)
    treatments = TreatmentThesis.objects.filter(
        thesis__field_trial_id__in=trialIds)
    treatmentData = []
    probelte = Vendor.objects.get(name='Probelte').id
    thesisIds = set()
    for ttreatment in treatments:
        # filter treatments that are not probelte product
        rate = 0
        if ttreatment.treatment.product.name == UNTREATED:
            rate = 0
            unit = 'l'
        elif ttreatment.treatment.product.vendor_id == probelte:
            rate = ttreatment.treatment.rate
            unit = ttreatment.treatment.rate_unit.name
        else:
            continue

        thesisId = ttreatment.thesis.id
        thesisIds.add(thesisId)
        treatmentData.append(
            {'thesis_id': thesisId,
             'trial_id': ttreatment.thesis.field_trial_id,
             'rate': rate,
             'unit': unit})
    exportCsvFile('./thesis_data', treatmentData)

    applications = Application.objects.filter(field_trial_id__in=trialIds)
    applicationsData = []
    for application in applications:
        applicationsData.append({
            'trial_id': application.field_trial.id,
            'app_date': application.app_date,
            'daf': application.daf})
    exportCsvFile('./applications', applicationsData)

    datasReplica = ReplicaData.objects.filter(
        reference__thesis__in=thesisIds,
        assessment__rate_type__name__in=['PESINC']).order_by(
            'reference__thesis__id',
            'assessment__assessment_date')

    dataPoints = []
    for dataPoint in datasReplica:
        dataPoints.append({
            'thesis_id': dataPoint.reference.thesis.id,
            'replica_id': dataPoint.reference.id,
            'value': dataPoint.value,
            'date': dataPoint.assessment.assessment_date,
            'unit': dataPoint.assessment.rate_type.getName()
        })
    exportCsvFile('./datapoints', dataPoints)

    weatherData = []
    for trial in trials:
        weatherInfo = Weather.objects.filter(
                latitude=trial['latitude'],
                longitude=trial['longitude']
            ).values(
                'date',
                'max_temp', 'min_temp', 'mean_temp',
                'soil_temp_0_to_7cm', 'soil_moist_0_to_7cm',
                'dew_point', 'relative_humidity', 'precipitation',
                'precipitation_hours', 'max_wind_speed'
            ).order_by('date')
        for weatherInfoDate in weatherInfo:
            weatherInfoDate['trial_id'] = trial['id']
            weatherData.append(weatherInfoDate)
    exportCsvFile('./weather_data', weatherData)


def weatherInfo(trial, assdate):
    dimensions = [
        'max_temp', 'min_temp', 'mean_temp',
        'soil_temp_0_to_7cm', 'soil_moist_0_to_7cm',
        'dew_point', 'relative_humidity', 'precipitation',
        'precipitation_hours', 'max_wind_speed']

    assLastDate = assdate - relativedelta(days=1)
    weatherInfo = Weather.objects.filter(
            date__range=(assdate - relativedelta(days=8),
                         assLastDate),
            latitude=trial.latitude,
            longitude=trial.longitude
        ).values('date', *dimensions).order_by('date')

    toReturn = {}
    toAvg = {3: {}, 5: {}, 7: {}}
    for wItem in weatherInfo:
        for dimension in dimensions:
            diffDays = (assLastDate - wItem['date']).days
            value = wItem[dimension]
            if wItem['date'] == assLastDate:
                toReturn[dimension] = value
            for days in toAvg:
                if diffDays < days:
                    if dimension not in toAvg[days]:
                        toAvg[days][dimension] = 0
                    toAvg[days][dimension] += value
    for days in toAvg:
        for dimension in toAvg[days]:
            avg = round(toAvg[days][dimension]/days, 2)
            toReturn[f'{dimension}_{days}'] = avg
    return toReturn


def getCfu(treatment, volume):
    cfuLiquido = 1  # 10E11 CFU/L
    cfuSolido = 10  # 10E10 CFU/g
    rate = 0
    if treatment.rate_unit.name == 'mL/L':
        rate = treatment.rate / 1000
        cfuP = cfuLiquido
    elif treatment.rate_unit.name == 'L/ha':
        rate = treatment.rate / volume
        cfuP = cfuLiquido
    elif treatment.rate_unit.name == 'Kg/ha':
        rate = treatment.rate / volume
        cfuP = cfuSolido
    else:
        return None
    cfu = rate * cfuP
    return cfu


def saveDataPoint(dataPoint, referenceData, dapa,
                  weatherData, progress, trial,
                  ttreatment, assmt):
    cfu = getCfu(ttreatment.treatment,
                 trial.application_volume)
    if not cfu:
        print(f'No managed unit for {trial.code} - '
              f'{assmt.assessment_date}')
    return {
        'trial_id': trial.id,
        'thesis_id': ttreatment.thesis_id,
        'assmt_id': assmt.id,
        'date': dataPoint.assessment.assessment_date,
        'repl_id': dataPoint.reference.id,
        'value': Abbott.do(
            dataPoint.value,
            referenceData[dataPoint.reference.number])/100,
        # treatment values
        'cfu': cfu,
        #  unit = ttreatment.treatment.rate_unit.name
        # value assessments
        'dapa': dapa,  # days after previous aplication
        'progress': progress,  # number of the evaluation in %
        # values trials
        'irrigation': trial.irrigation.name,
        'mode': trial.mode.name,
        'soil': trial.soil,
        'cultivation': trial.cultivation.name,
        # weather info
        **weatherData}


def extractDataset():
    probelte = Vendor.objects.get(name='Probelte').id
    trials = FieldTrial.objects.filter(
        plague=Plague.objects.get(other='Botrytis'),
        crop=Crop.objects.get(name='Strawberry'))
    dataPoints = []
    for trial in trials:
        applications = Application.getObjects(trial).order_by('app_date')
        treatments = TreatmentThesis.objects.filter(
            thesis__field_trial_id=trial.id)
        assmts = Assessment.getObjects(trial).order_by('assessment_date')
        numAss = len(assmts)
        countAss = 0
        for assmt in assmts:
            if assmt.rate_type.name != 'PESINC':
                continue

            # Days after previous application
            dapa = 0
            for app in applications:
                check = (assmt.assessment_date - app.app_date).days
                if check <= 0:
                    break
                dapa = check

            # Progress evaluation
            progress = round(countAss / numAss, 2)
            countAss += 1
            weatherData = weatherInfo(trial, assmt.assessment_date)

            referenceData = {
                item.reference.number: item.value
                for item in ReplicaData.objects.filter(
                    reference__thesis_id=trial.control_thesis,
                    assessment=assmt)}

            for ttreatment in treatments:
                if ttreatment.thesis_id == trial.control_thesis:
                    continue
                if ttreatment.treatment.product.vendor_id != probelte:
                    continue
                replicaData = ReplicaData.objects.filter(
                    reference__thesis_id=ttreatment.thesis_id,
                    assessment=assmt)

                for dataPoint in replicaData:
                    dataPoints.append(saveDataPoint(
                        dataPoint,  referenceData, dapa, weatherData,
                        progress, trial, ttreatment, assmt))
    exportCsvFile('./datapoints', dataPoints)


seriesDates = {
    'SO': '2022-12-15',
    'S1': '2022-12-26',
    'S2': '2023-01-02',
    'S3': '2023-01-30',
    'S4': '2023-02-13',
    'S5': '2023-02-27',
    'S6': '2023-03-27'}


def to_float(value):
    try:
        value = value.replace(',', '.')
        return float(value)
    except ValueError:
        return None


def trimMeanStdDev(data, threshold=2):
    mean = np.mean(data)
    std_dev = np.std(data)
    if std_dev == 0:
        return mean

    # Calculate the z-scores for each data point
    z_scores = [(x - mean) / std_dev for x in data]

    # Define the threshold for outliers
    # (e.g., more than 2 standard deviations away)

    # Remove outliers
    filtered_data = [x for x, z in zip(data, z_scores) if abs(z) <= threshold]

    # Calculate the average of the filtered data
    return np.mean(filtered_data)


def test_trimMean():
    data = [277, 245, 109000, 1530]
    trimMean = trimMeanStdDev(data)
    mean = np.mean(data)
    return trimMean, mean


def importQpcr(trial, fileName, part_rated):
    with open(fileName) as csvfile:
        reader = csv.DictReader(csvfile, delimiter=';')
        for row in reader:
            ratio = to_float(row['Ratio   '])
            cq = to_float(row['Cq   '])
            if not cq:
                continue

            gene = row['Gene Name']
            rateName = gene.replace(' ', '')
            rate_type_ratio = RateTypeUnit.findOrCreate(
                name=rateName + ' Ratio Cq',
                unit='Ratio Cq')
            rate_type_cq = RateTypeUnit.findOrCreate(
                name=rateName + ' Cq',
                unit='Cq')
            timestamp = row['Sample Name']
            blocks = timestamp.split(' ')
            series = blocks[0]
            dateAss = seriesDates.get(series, None)
            if not dateAss:
                continue
            assmt_cq = Assessment.findOrCreate(
                name=f'{series} {rateName}',
                part_rated=part_rated,
                assessment_date=dateAss,
                field_trial=trial,
                crop_stage_majority='-',
                rate_type=rate_type_cq)
            assmt_ratio = Assessment.findOrCreate(
                name=f'{series} {rateName}',
                part_rated=part_rated,
                assessment_date=dateAss,
                field_trial=trial,
                crop_stage_majority='-',
                rate_type=rate_type_ratio)
            replicaName = blocks[1]
            replicas = Replica.objects.filter(
                thesis__field_trial_id=trial.id,
                name=replicaName)
            if not replicas:
                print(f'ERROR, replica {replicaName} should exists')
                break
            sampleNumber = int(blocks[2][1])
            sample = Sample.findOrCreate(replica=replicas[0],
                                         number=sampleNumber)
            SampleData.findOrCreate(
                reference=sample, assessment=assmt_cq,
                value=cq)
            if ratio:
                SampleData.findOrCreate(
                    reference=sample, assessment=assmt_ratio,
                    value=ratio)


def importQpcrFiles():
    folder_path = '../RawdataqPCR'
    trial = FieldTrial.objects.get(code='20230502')
    # Loop through all files in the folder and its subdirectories
    for foldername, subfolders, filenames in os.walk(folder_path):
        for filename in filenames:
            # Get the full path of the file
            fileName = os.path.join(foldername, filename)

            # Check if the path points to a file (not a directory)
            if fileName.split('.')[-1] == 'csv':
                print(f"Import {fileName}")
                part_rated = None
                if 'Fresa' in filename:
                    part_rated = PartRated.FRUIT
                elif 'Hoja' in filename:
                    part_rated = PartRated.LEAF
                else:
                    continue
                importQpcr(trial, fileName, part_rated)


def calculateReplicaValues():
    trial = FieldTrial.objects.get(code='20230502')
    replicas = Replica.getFieldTrialObjects(trial)
    for unit in ['Ratio Cq', 'Cq']:
        rate_units = RateTypeUnit.objects.filter(unit=unit)

        for rate_unit in rate_units:
            for asstm in Assessment.objects.filter(
                    rate_type=rate_unit,
                    field_trial_id=trial.id):
                for replica in replicas:
                    values = SampleData.objects.values(
                        'value'
                    ).filter(
                        reference__replica_id=replica.id,
                        assessment_id=asstm.id)
                    if values:
                        data = [v['value'] for v in values]
                        trimMean = trimMeanStdDev(data)

                        ReplicaData.findOrCreate(
                            assessment_id=asstm.id,
                            reference_id=replica.id,
                            value=trimMean)


def importQPCR():
    importQpcrFiles()
    calculateReplicaValues()


if __name__ == '__main__':
    # cleanPlagues()
    # importConcreateCSV()
    # createThesisTreatments()
    # importOne()
    # exportPdf()
    # importOneMapa()
    # discoverReports()
    # testArchive()
    # extractData()
    # extractDataset()
    test_trimMean()
    # importQPCR()
