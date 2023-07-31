from datetime import datetime
from django.test import TestCase
from baaswebapp.models import ModelHelpers
from baaswebapp.data_loaders import TrialDbInitialLoader
from trialapp.models import Crop, Plague, FieldTrial, \
                            Thesis, Replica
from trialapp.data_models import ReplicaData
from trialapp.import_pdf_trial import ImportPdfTrial, TrialTags, \
     AssmtTableSimpleHeader


class ImportPdfTest(TestCase):

    _importer = None
    _root = '/Users/jsantiago/Library/CloudStorage/OneDrive-PROBELTE,SAU/'\
            'Data/estudios/testing/'

    def loader(self, filename, debug=False):
        importer = ImportPdfTrial(filename, debugInfo=debug)
        result = importer.walkThrough()
        self.assertTrue(result)
        self.assertTrue(importer._trial is not None)
        return importer

    def setUp(self):
        TrialDbInitialLoader.loadInitialTrialValues()
        self._filename = self._root+'20150201 BOTRYBEL EFICACIA FRESÓN 01.pdf'
        self._filename2 = \
            self._root+'20171102 BOTRYBEL EFICACIA CPCP PEPINO PORTUGAL 09.pdf'
        self._filename3 = \
            self._root+'20180302 BOTRYBEL EFICACIA FRUTAL DE HUESO 03.pdf'

        # Thesis are in first column. They look like this:
        # '1 PB00112 mL/L'
        # '[thesisnumber] [prod][dosis] [Replica1]'
        # Notice that there is no space between product and dosis
        # For the sake of identify thesis, we use put it together
        #
        # In this case, the first thesis are not in the first line
        # noqa: E501 |    | Pest Type                     |   Unnamed: 0 | Unnamed: 1   |   Unnamed: 2 | D  Disease      | D  Disease.1    | D  Disease.2    |
        # noqa: E501 |---:|:------------------------------|-------------:|:-------------|-------------:|:----------------|:----------------|:----------------|
        # noqa: E501 |  0 | Pest Code                     |          nan | nan          |          nan | MONIFG          | MONIFG          | MONIFG          |
        # noqa: E501 |  1 | Pest Scientific Name          |          nan | nan          |          nan | Monilinia fruc> | Monilinia fruc> | Monilinia fruc> |
        # ....
        # noqa: E501 | 23 | Trt Treatment Rate            |          nan | Appl         |          nan | nan             | nan             | nan             |
        # noqa: E501 | 24 | No. Name Rate Unit            |          nan | Code Plot    |          nan | 19              | 24              | 29              |
        # noqa: E501 | 25 | 1PB001 4,0 L/ha               |          nan | ABCD 105     |          nan | 0,00            | 0,00            | 4,00            |
        # noqa: E501 | 26 | nan                           |          nan | 202          |          nan | 0,00            | 0,00            | 1,00            |
        # noqa: E501 | 27 | nan                           |          nan | 306          |          nan | 0,00            | 0,00            | 2,00            |
        # noqa: E501 | 28 | nan                           |          nan | 405          |          nan | 0,00            | 0,00            | 3,00            |
        # noqa: E501 | 29 | nan                           |          nan | Mean =       |          nan | 0,00            | 0,00            | 2,50            |
        # noqa: E501 | 30 | 2PB001 8,0 L/ha               |          nan | ABCD 102     |          nan | 0,00            | 0,00            | 2,00            |

    def test_singlelineTables(self):
        importer = self.loader(self._filename3)

        firstTable = importer._evals[0]
        importer._debug = True
        importer.printTable(firstTable._table)
        self.assertTrue(isinstance(firstTable, AssmtTableSimpleHeader))
        self.assertEqual(firstTable._firstRowValuesNames, 25)
        self.assertEqual(firstTable._indexReplicaColumn, 2)
        self.assertEqual(firstTable._indexfirstColumnWithValues, 4)

        # Find assessments
        firstTable.findTagPositions()
        columnToExplore = firstTable._columns[
            firstTable._indexfirstColumnWithValues]
        assesment = firstTable.extractAssessmentInfo(columnToExplore)
        self.assertEqual(assesment.assessment_date,
                         datetime(2018, 1, 9, 0, 0))
        self.assertEqual(assesment.crop_stage_majority, '81')
        self.assertEqual(assesment.name, '0 DA-C')

        assessmentSet = firstTable.extractAssessmentInfo(columnToExplore)
        self.assertEqual(assessmentSet.unit.name, '%')
        self.assertEqual(assessmentSet.type.name, 'PESINC')

        # Find thesis
        firstTable.prepareThesis()
        replicasNumber = firstTable.extractThesis()
        self.assertEqual(replicasNumber, 24)
        thesis = Thesis.getObjects(importer._trial)
        self.assertEqual(len(thesis), 6)
        self.assertEqual(thesis[5].name, 'Untreated Check')
        self.assertEqual(thesis[5].number, 6)
        self.assertEqual(thesis[0].name, 'PB001 4,0 L/ha')
        self.assertEqual(thesis[0].number, 1)

        firstTable.extractAssessmentData(
            columnToExplore, assesment, assessmentSet)
        replicaData = ReplicaData.objects.all()
        self.assertEqual(len(firstTable._replicaDict.keys()),
                         len(replicaData))
        firstReplica = firstTable._replicaDict[firstTable._firstRowValuesNames]
        self.assertEqual(replicaData[0].reference.name,
                         firstReplica.name)
        self.assertEqual(replicaData[0].reference.name, '105')
        self.assertEqual(replicaData[0].value, 0.00)

        lastReplica = firstTable._replicaDict[53]
        self.assertEqual(lastReplica.name, '404')
        self.assertEqual(replicaData[23].value, 0.00)
        self.assertEqual(replicaData[23].reference.name, '404')

        # Load last columns
        columnToExplore2 = firstTable._columns[firstTable._numberColumns-1]
        assesment2 = firstTable.extractAssessmentInfo(columnToExplore2)
        self.assertEqual(assesment2.assessment_date,
                         datetime(2018, 9, 15, 0, 0))
        self.assertEqual(assesment2.crop_stage_majority, '87-89')
        self.assertEqual(assesment2.name, '7 DA-D')

        assessmentSet2 = firstTable.extractAssessmentInfo(columnToExplore2)
        self.assertEqual(assessmentSet2.unit.name, '%')
        self.assertEqual(assessmentSet2.type.name, 'PESINC')

        firstTable.extractAssessmentData(
            columnToExplore2, assesment2, assessmentSet2)

        firstReplicaLastColumn = ReplicaData.objects.filter(
            reference=firstReplica, assesment=assesment2,
            unit=assessmentSet2)
        self.assertEqual(firstReplicaLastColumn[0].value, 4.00)

        lastReplicaLastColumn = ReplicaData.objects.filter(
            reference=lastReplica, assesment=assesment2,
            unit=assessmentSet2)
        self.assertEqual(lastReplicaLastColumn[0].value, 8.00)

    def test_singlelineTablesBasics(self):
        importer = self.loader(self._filename3)
        firstTable = importer._evals[0]
        importer.printTable(firstTable._table)
        firstTable.findTagPositions()
        firstTable.getCrop()
        self.assertEqual(firstTable._trial.crop.name,
                         'Peach')
        firstTable.getPest()
        self.assertEqual(firstTable._trial.plague.name,
                         'Moniliosis')

    def test_importFileBasics(self):
        importer = self.loader(self._filename)
        self.assertEqual(importer._trial.product.name,
                         'Botrybel')
        self.assertEqual(importer._trial.code, '20150201')  # '20171102')
        unknownLabel = ModelHelpers.UNKNOWN
        self.assertEqual(importer._trial.crop.name,
                         unknownLabel)
        self.assertEqual(importer._trial.plague.name,
                         unknownLabel)
        # pepino = Crop.objects.get(name='Cucumber')
        fresa = Crop.objects.get(name='Strawberry')
        botrytis = Plague.objects.get(name='Botrytis')
        firstTable = importer._evals[0]
        firstTable.findTagPositions()
        # There is something funny here. From another test, this is persisted?
        importer._debug = True
        firstTable.getCrop()
        self.assertEqual(firstTable._trial.crop.name,
                         fresa.name)
        firstTable.getPest()
        self.assertEqual(firstTable._trial.plague.name,
                         botrytis.name)
        importer._trial = FieldTrial.objects.get(pk=firstTable._trial.id)
        self.assertEqual(importer._trial.crop.name,
                         fresa.name)
        self.assertEqual(importer._trial.plague.name,
                         botrytis.name)

    def test_skipRTableNoReplicas(self):
        importer = self.loader(self._filename2)
        # This process will skip any statistical table
        for anyTable in importer._evals:
            anyTable.prepareThesis()
            replicasNumber = anyTable.extractThesis()
            self.assertTrue(replicasNumber > 0)

    def test_extractEvaluations(self):
        importer = self.loader(self._filename)
        firstTable = importer._evals[0]
        firstTable.prepareThesis()
        firstTable.extractThesis()
        columnName = firstTable._table.columns[1]

        firstTable.findTagPositions()
        self.assertEqual(firstTable._tagPositions[TrialTags.RATING_DATE],
                         11)
        # Check that if it is not in the dict, we get default
        pitopato = firstTable.getTagPositionValue(
            firstTable._table.columns[1], 'PITOPATO', '696')
        self.assertEqual(pitopato, '696')

        # 'Pest Type\rPest Code\rPest Scientific Name\rPest Name\rCrop Code\r
        # BBCH Scale\rCrop Scientific Name\rCrop Name\rCrop Variety\r
        # Description\rPart Rated\rRating Date\rRating Type\rRating Unit\r
        # Sample Size, Unit\rNumber of Subsamples\rCrop Stage Majority\r
        # Crop Stage Scale\rPest Stage Majority\rFootnote Number\r
        # Days After First/Last Applic.\r
        # Trt-Eval Interval\rARM Action Codes\rNumber of Decimals'

        assesment = firstTable.extractAssessmentInfo(columnName)
        self.assertEqual(assesment.assessment_date,
                         datetime(2015, 2, 18, 0, 0))
        self.assertEqual(assesment.crop_stage_majority,
                         '85')
        self.assertEqual(assesment.name,
                         '0 DA-A')
        assessmentSet = firstTable.extractAssessmentInfo(columnName)
        self.assertEqual(assessmentSet.unit.name, 'NUMBER')
        self.assertEqual(assessmentSet.type.name, 'FRUIT')

        # check formats
        self.assertEqual(firstTable.convertToFloat('3.145'),
                         3.145)
        self.assertEqual(firstTable.convertToFloat('3,145'),
                         3.145)
        self.assertEqual(firstTable.convertToFloat('3.145a'),
                         None)
        firstTable.extractAssessmentData(
            columnName, assesment, assessmentSet)
        replicaData = ReplicaData.objects.all()
        numberData = 0
        for key in firstTable._replicaDict:
            numberData += len(firstTable._replicaDict[key])
        self.assertEqual(len(replicaData), numberData)
        self.assertEqual(replicaData[0].value, 201.00)
        self.assertEqual(replicaData[0].reference.name, '106')
        self.assertEqual(replicaData[15].value, 204.00)
        self.assertEqual(replicaData[15].reference.name, '404')

    def test_extractThesisReplicas(self):
        importer = self.loader(self._filename)
        firstTable = importer._evals[0]
        firstTable.prepareThesis()
        replicasNumber = firstTable.extractThesis()
        self.assertEqual(replicasNumber, 24)
        thesis = Thesis.getObjects(importer._trial)
        self.assertEqual(len(thesis), 6)
        self.assertEqual(thesis[3].name, 'PB0503500 g/ha')
        self.assertEqual(thesis[0].name, 'PB00112 mL/L')
        # self.assertEqual(thesis[5].name, 'Untreated Check ')
        replicasOne = Replica.getObjects(thesis[0])
        self.assertEqual(len(replicasOne), 4)
        self.assertEqual(replicasOne[0].name, '106')

# # noqa: E501 |    | Pest Type                     |   Unnamed: 0 | Unnamed: 1   |   Unnamed: 2 | D  Disease      | D  Disease.1    | D  Disease.2    |
# # noqa: E501 |---:|:------------------------------|-------------:|:-------------|-------------:|:----------------|:----------------|:----------------|
# # noqa: E501 |  0 | Pest Code                     |          nan | nan          |          nan | MONIFG          | MONIFG          | MONIFG          |
# # noqa: E501 |  1 | Pest Scientific Name          |          nan | nan          |          nan | Monilinia fruc> | Monilinia fruc> | Monilinia fruc> |
# # noqa: E501 |  2 | Pest Name                     |          nan | nan          |          nan | Blossom blight> | Blossom blight> | Blossom blight> |
# # noqa: E501 |  3 | Crop Code                     |          nan | nan          |          nan | PRNPS           | PRNPS           | PRNPS           |
# # noqa: E501 |  4 | BBCH Scale                    |          nan | nan          |          nan | BSTO            | BSTO            | BSTO            |
# # noqa: E501 |  5 | Crop Scientific Name          |          nan | nan          |          nan | Prunus persica  | Prunus persica  | Prunus persica  |
# # noqa: E501 |  6 | Crop Name                     |          nan | nan          |          nan | Peach           | Peach           | Peach           |
# # noqa: E501 |  7 | Crop Variety                  |          nan | nan          |          nan | Rojo de Albesa  | Rojo de Albesa  | Rojo de Albesa  |
# # noqa: E501 |  8 | Part Rated                    |          nan | nan          |          nan | FRUIT  P        | FRUIT  P        | FRUIT  P        |
# # noqa: E501 |  9 | Rating Date                   |          nan | nan          |          nan | 01/09/2018      | 08/09/2018      | 15/09/2018      |
# # noqa: E501 |  10 | Rating Type                   |          nan | nan          |          nan | PESINC          | PESINC          | PESINC          |
# # noqa: E501 |  11 | Rating Unit                   |          nan | nan          |          nan | %               | %               | %               |
# # noqa: E501 |  12 | Sample Size, Unit             |          nan | nan          |          nan | 100FRUIT        | 100FRUIT        | 100FRUIT        |
# # noqa: E501 |  13 | Collection Basis, Unit        |          nan | nan          |          nan | 1PLOT           | 1PLOT           | 1PLOT           |
# # noqa: E501 |  14 | Number of Subsamples          |          nan | nan          |          nan | 1               | 1               | 1               |
# # noqa: E501 |  15 | Crop Stage Majority           |          nan | nan          |          nan | 81              | 85-87           | 87-89           |
# # noqa: E501 |  16 | Crop Stage Scale              |          nan | nan          |          nan | BBCH            | BBCH            | BBCH            |
# # noqa: E501 |  17 | Footnote Number               |          nan | nan          |          nan | 3               | 3               | 3               |
# # noqa: E501 |  18 | Days After First/Last Applic. |          nan | nan          |          nan | 159149          | 1667            | 1737            |
# # noqa: E501 |  19 | Trt-Eval Interval             |          nan | nan          |          nan | 0 DA-C          | 0 DA-D          | 7 DA-D          |
# # noqa: E501 |  20 | Plant-Eval Interval           |          nan | nan          |          nan | nan             | nan             | nan             |
# # noqa: E501 |  21 | ARM Action Codes              |          nan | nan          |          nan | TIO[17]         | TIO[22]         | TIO[27]         |
# # noqa: E501 |  22 | Number of Decimals            |          nan | nan          |          nan | 2               | 2               | 2               |
# # noqa: E501 |  23 | Trt Treatment Rate            |          nan | Appl         |          nan | nan             | nan             | nan             |
# # noqa: E501 |  24 | No. Name Rate Unit            |          nan | Code Plot    |          nan | 19              | 24              | 29              |
# # noqa: E501 |  25 | 1PB001 4,0 L/ha               |          nan | ABCD 105     |          nan | 0,00            | 0,00            | 4,00            |
# # noqa: E501 |  26 | nan                           |          nan | 202          |          nan | 0,00            | 0,00            | 1,00            |
# # noqa: E501 |  27 | nan                           |          nan | 306          |          nan | 0,00            | 0,00            | 2,00            |
# # noqa: E501 |  28 | nan                           |          nan | 405          |          nan | 0,00            | 0,00            | 3,00            |
# # noqa: E501 |  29 | nan                           |          nan | Mean =       |          nan | 0,00            | 0,00            | 2,50            |
# # noqa: E501 |  30 | 2PB001 8,0 L/ha               |          nan | ABCD 102     |          nan | 0,00            | 0,00            | 2,00            |
# # noqa: E501 |  31 | nan                           |          nan | 204          |          nan | 0,00            | 0,00            | 2,00            |
# # noqa: E501 |  32 | nan                           |          nan | 303          |          nan | 0,00            | 0,00            | 2,00            |
# # noqa: E501 |  33 | nan                           |          nan | 406          |          nan | 0,00            | 0,00            | 3,00            |
# # noqa: E501 |  34 | nan                           |          nan | Mean =       |          nan | 0,00            | 0,00            | 2,25            |
# # noqa: E501 |  35 | 3PB001 15,0 L/ha              |          nan | ABCD 101     |          nan | 0,00            | 0,00            | 1,00            |
# # noqa: E501 |  36 | nan                           |          nan | 203          |          nan | 0,00            | 0,00            | 1,00            |
# # noqa: E501 |  37 | nan                           |          nan | 304          |          nan | 0,00            | 0,00            | 1,00            |
# # noqa: E501 |  38 | nan                           |          nan | 403          |          nan | 0,00            | 0,00            | 2,00            |
# # noqa: E501 |  39 | nan                           |          nan | Mean =       |          nan | 0,00            | 0,00            | 1,25            |
# # noqa: E501 |  40 | 4PB050 4,0 kg/ha              |          nan | ABCD 104     |          nan | 0,00            | 0,00            | 3,00            |
# # noqa: E501 |  41 | nan                           |          nan | 201          |          nan | 0,00            | 0,00            | 1,00            |
# # noqa: E501 |  42 | nan                           |          nan | 301          |          nan | 0,00            | 0,00            | 1,00            |
# # noqa: E501 |  43 | nan                           |          nan | 402          |          nan | 0,00            | 0,00            | 1,00            |
# # noqa: E501 |  44 | nan                           |          nan | Mean =       |          nan | 0,00            | 0,00            | 1,50            |
# # noqa: E501 |  45 | 5SERENADE MAX 4,0 kg/ha       |          nan | ABCD 103     |          nan | 0,00            | 0,00            | 2,00            |
# # noqa: E501 |  46 | nan                           |          nan | 206          |          nan | 0,00            | 0,00            | 2,00            |
# # noqa: E501 |  47 | nan                           |          nan | 302          |          nan | 0,00            | 0,00            | 1,00            |
# # noqa: E501 |  48 | nan                           |          nan | 401          |          nan | 0,00            | 0,00            | 1,00            |
# # noqa: E501 |  49 | nan                           |          nan | Mean =       |          nan | 0,00            | 0,00            | 1,50            |
# # noqa: E501 |  50 | 6Untreated Check              |          nan | 106          |          nan | 0,00            | 0,00            | 8,00            |
# # noqa: E501 |  51 | nan                           |          nan | 205          |          nan | 0,00            | 0,00            | 7,00            |
# # noqa: E501 |  52 | nan                           |          nan | 305          |          nan | 0,00            | 0,00            | 9,00            |
# # noqa: E501 |  53 | nan                           |          nan | 404          |          nan | 0,00            | 0,00            | 8,00            |
# # noqa: E501 |  54 | nan                           |          nan | Mean =       |          nan | 0,00            | 0,00            | 8,00            |

    def test_extractThesisReplicasSameColumn(self):
        thisFilename = self._root+'20110202 BOTRYBEL EFICACIA FRESÓN 02.pdf'
        importer = self.loader(thisFilename)
        firstTable = importer._evals[0]
        importer.printTable(firstTable._table)
        firstTable.findTagPositions()
        firstTable.prepareThesis()
        replicasNumber = firstTable.extractThesis()
        self.assertEqual(replicasNumber, 20)
        thesis = Thesis.objects.filter(
            field_trial=firstTable._trial).all()
        self.assertEqual(len(thesis), 5)
        self.assertTrue(Replica.objects.filter(
            thesis=thesis[0],
            number=4).exists())

    def test_similarThesisnames(self):
        thisFilename = self._root+'20170501 BOTRYBEL EFICACIA FRESÓN 09.pdf'
        importer = self.loader(thisFilename)
        for table in importer._evals:
            table.prepareThesis()
            table.findTagPositions()
            table.extractThesis()

        numberThesis = len(Thesis.getObjects(importer._trial))
        self.assertEqual(numberThesis, 5)

    def test_extractThesisName(self):
        thisFilename = self._root+'20110202 BOTRYBEL EFICACIA FRESÓN 02.pdf'
        importer = self.loader(thisFilename)
        tlb = importer._evals[0]
        number, name, firstReplica = tlb.extractThesisInfo(
            '1Untreated Check101')
        self.assertEqual(number, 1)
        self.assertEqual(name, 'Untreated Check')
        self.assertEqual(firstReplica, '101')

        number, name, firstReplica = tlb.extractThesisInfo('1Untreated Check')
        self.assertEqual(number, 1)
        self.assertEqual(name, 'Untreated Check')
        self.assertEqual(firstReplica, None)

        number, name, firstReplica = tlb.extractThesisInfo(
            'Untreated Check101')
        self.assertEqual(number, None)
        self.assertEqual(name, 'Untreated Check')
        self.assertEqual(firstReplica, '101')

        number, name, firstReplica = tlb.extractThesisInfo(
            '2P B0014,8 l/ha105')
        self.assertEqual(number, 2)
        self.assertEqual(name, 'P B0014,8 l/ha')
        self.assertEqual(firstReplica, '105')

        number, name, firstReplica = tlb.extractThesisInfo(
            '5SERENADE MAX 4,0 kg/ha')
        self.assertEqual(number, 5)
        self.assertEqual(name, 'SERENADE MAX 4,0 kg/ha')
        self.assertEqual(firstReplica, None)

        number, name, firstReplica = tlb.extractThesisInfo(
            '4 PB00115,0 L/haABCD10')
        self.assertEqual(number, 4)
        self.assertEqual(name, 'PB00115,0 L/ha10')
        self.assertEqual(firstReplica, None)

        number, name, firstReplica = tlb.extractThesisInfo(
            '14 PB00115,0 L/haABCD101')
        self.assertEqual(number, 14)
        self.assertEqual(name, 'PB00115,0 L/ha')
        self.assertEqual(firstReplica, '101')

        info = '1 PB00112 mL/L ABCD 106\r204\r301\r403\rMean ='
        number, name, firstReplica = tlb.extractThesisInfo(info)
        self.assertEqual(number, 1)
        self.assertEqual(name, 'PB00112 mL/L')
        self.assertEqual(firstReplica, '106')
        self.assertEqual(
            tlb.extractReplicasNames(info),
            ['106', '204', '301', '403'])

        info = '1PB00112mL/LABCD106\r204\r301\r403\rMean ='
        number, name, firstReplica = tlb.extractThesisInfo(info)
        self.assertEqual(number, 1)
        self.assertEqual(name, 'PB00112mL/L')
        self.assertEqual(firstReplica, '106')
        self.assertEqual(
            tlb.extractReplicasNames(info),
            ['106', '204', '301', '403'])

    def test_differentLanguages(self):
        thisFilename = self._root + \
            '20220905 INFORME FINAL  SoilEkky WP Lechuga  BAAS.pdf'
        importer = self.loader(thisFilename)
        importer.run()
        self.assertTrue('C; LACSA', importer._trial.crop.name)
