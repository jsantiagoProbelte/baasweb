import os
from PyPDF2 import PdfReader
import docx2txt
import shutil
from trialapp.models import FieldTrial, ModelHelpers
import datetime


# Utilities to generate Field Trial from existing reports
class ReportFinder:
    _actionDiscover = False
    _actionImporter = False
    _baseDir = None
    _discoverDir = None
    _importDir = None
    _parkDir = None
    _rejectDir = None
    PDF_TYPE = 'pdf'
    DOC_TYPE = 'doc'
    SUPPORTED_FILES = ['pdf', 'doc', 'docx']
    ACTION_DISCOVER = 'discover'
    ACTION_IMPORTER = 'import'
    _keysDiscover = [
        'efficacy', 'field test', 'field trial', 'ensayo de campo',
        'ensayos eficacia', 'estudio de eficacia']
    _keys = None

    def __init__(self, baseDir='.', action=ACTION_DISCOVER) -> None:
        self._baseDir = baseDir
        if baseDir[-1] != '/':
            self._baseDir += '/'
        self._discoverDir = self.getDiscoverPath()
        self._importDir = self._baseDir + ReportFinder.ACTION_IMPORTER + '/'
        self._parkDir = self._baseDir + 'parked'
        self._rejectDir = self._baseDir + 'rejected' + '/'
        if action == ReportFinder.ACTION_IMPORTER:
            self.getTokensFieldTrial()
            self._actionImporter = True

    def getDiscoverPath(self):
        return self._baseDir + ReportFinder.ACTION_DISCOVER + '/'

    def run(self, dirList, discover=True, importer=False):
        self._actionImporter = importer
        self._actionDiscover = discover
        if dirList is None:
            dirList = [self.getDiscoverPath()]
        self.finder(dirList)

    # Scan directories to identify potential files containing
    # field trial information
    def finder(self, dirList):
        stats = self.createStats()
        if self._actionImporter:
            self.getTokensFieldTrial()

        for dirIn in dirList:
            print('--------Searching in {}'.format(dirIn))
            dirStats = self.scanDir(dirIn)
            self.sumStats(stats, dirStats)
        print('Results. {}'.format(stats))

    def copyFile(self, origin, success):
        # copy2 preserves file metadata
        if success:
            shutil.copy2(origin, self._discoverDir)

    def moveFile(self, filename, success):
        # copy2 preserves file metadata
        targetDir = self._importDir if success else self._rejectDir
        origin = self._discoverDir + filename
        if not os.path.exists(targetDir + filename):
            shutil.move(origin, targetDir, copy_function=shutil.copy2)

    def readPDF(self, filename):
        try:
            pdfReader = PdfReader(filename)
            # Discerning the number of pages will allow us to parse through
            # all the pages.
            num_pages = len(pdfReader.pages)
            # The while loop will read each page.
            count = 0
            text = ''
            while count < num_pages:
                pageObj = pdfReader.pages[count]
                otext = pageObj.extract_text(0)
                count += 1
                text += otext.lower()
                count+1
            return text
        except Exception:
            return None

    def readDoc(self, filename):
        try:
            otext = docx2txt.process(filename)
            return otext.lower()
        except Exception:
            return None

    def createStats(self):
        return {key: {'totals': 0,
                      'discovered': 0,
                      'imported': 0}
                for key in ['summary',
                            ReportFinder.DOC_TYPE,
                            ReportFinder.PDF_TYPE]}

    def doStats(self, stats, fileType,
                successDiscover, successImporter):
        stats['summary']['totals'] += 1
        stats['summary']['discovered'] += 1 if successDiscover else 0
        stats['summary']['imported'] += 1 if successImporter else 0
        if fileType in stats:
            stats[fileType]['totals'] += 1
            stats[fileType]['discovered'] += 1 if successDiscover else 0
            stats[fileType]['imported'] += 1 if successImporter else 0
        if successImporter:
            result = 'Import'
        else:
            if successDiscover:
                result = 'Candidate'
            else:
                result = 'Discarded'
        return result

    def sumStats(self, totals, partial):
        for key in totals:
            for subkey in totals[key]:
                totals[key][subkey] += partial[key][subkey]

    def extractTextFromFile(self, root, filename):
        filepath = root+'/'+str(filename)
        if filename.endswith('.pdf'):
            return self.readPDF(filepath), ReportFinder.PDF_TYPE, filepath
        elif filename.endswith('.docx') or filename.endswith('.doc'):
            return self.readDoc(filepath), ReportFinder.DOC_TYPE, filepath
        else:
            return None, None, filepath

    def doAction(self, text, filename, filepath):
        successDiscover = None
        successImporter = None
        tryImport = self._actionImporter
        if text is None or text == '':
            return False, None
        if self._actionDiscover:
            successDiscover = self.doDiscoverAction(text)
            # if successDiscover is False, do not try import
            tryImport &= successDiscover
        if tryImport:
            successImporter = self.doImportAction(text, filename, filepath)
        return successDiscover, successImporter

    def postAction(self, filepath, filename,
                   successDiscover, successImporter):
        try:
            tryPostActionImporter = self._actionImporter
            if self._actionDiscover:
                self.copyFile(filepath, successDiscover)
                # if successDiscover is False, successImporter cannot be True
                tryPostActionImporter &= successDiscover
            if tryPostActionImporter:
                self.moveFile(filename, successImporter)
        except Exception:
            print('[Exception] post Action {}'.format(filename))

    def scanDir(self, inDir):
        stats = self.createStats()
        # skip = True
        for root, dirs, files in os.walk(os.path.realpath(inDir)):
            previousRoot = ''
            print('Root:{}'.format(root))
            print('Dirs:{}'.format(dirs))
            # if skip and 'ENSAYOS BIOFERTILIZANTES' in root:
            #     if '20210401 BIOPRON MAIZ FRANCIA BIOLINE' in root:
            #         skip = False
            #     else:
            #         print('[Skikking]{}'.format(root))
            #         continue
            for filename in files:
                successDiscover = False
                successImporter = False
                text, typeFile, filepath = self.extractTextFromFile(
                    root, filename)
                result = 'Ignored'
                if typeFile is not None:
                    successDiscover, successImporter = self.doAction(
                        text, filename, filepath)
                    self.postAction(
                        filepath, filename,
                        successDiscover, successImporter)
                    result = self.doStats(
                        stats, typeFile,
                        successDiscover, successImporter)
                if previousRoot != root:
                    previousRoot = root
                    print('....{}'.format(root))

                print("[{}]\t{}".format(result, filename))
        return stats

    def doDiscoverAction(self, text):
        for keyword in self._keysDiscover:
            if keyword in text:
                return True
        return False

    # Functions to import the report into db
    def getTokensFieldTrial(self):
        self._keys = {clase: {'keys': clase.getDictObjectsId(),
                              'no_key': clase.getUnknownKey().id}
                      for clase in FieldTrial.getForeignModels()}

    def scanImportKeys(self, text, clase):
        keywords = self._keys[clase]['keys']
        for keyword in keywords:
            # We keep the first one
            if keyword in text:
                return True, keywords[keyword]
        return False, self._keys[clase]['no_key']

    # Scan document to identify the key metadata elements to
    # generate a FieldTrial
    def scanAttributesFieldTrial(self, text):
        # Search for key information in the text
        foundAttributes = {}
        referedModels = FieldTrial.getForeignModels()
        anyFound = False
        for clase in referedModels:
            label = referedModels[clase]
            found, foundAttributes[label] = self.scanImportKeys(text, clase)
            anyFound = anyFound or found
        return anyFound, foundAttributes

    def dateIso(self, filepath, created):
        if created:
            tiempo = os.path.getctime(filepath)
        else:
            tiempo = os.path.getmtime(filepath)
        return datetime.date.fromtimestamp(tiempo).isoformat()

    def setFieldTrialDefaultValues(self, filename, filepath):
        return {
            'name': filename.split('.')[0],
            'initiation_date': self.dateIso(filepath, True),
            'completion_date': self.dateIso(filepath, False),
            'responsible': ModelHelpers.UNKNOWN,
            'contact': ModelHelpers.UNKNOWN,
            'location': ModelHelpers.UNKNOWN,
            'replicas_per_thesis': 0,
            'report_filename': self._importDir + filename,
            'blocks': 0}

    def doImportAction(self, text, filename, filepath):
        anyFound, attributes = self.scanAttributesFieldTrial(text)
        if anyFound:
            # Create FieldTrial object from found attributes.
            defaults = self.setFieldTrialDefaultValues(filename, filepath)
            values = {**defaults, **attributes}
            print('++ Creating field trial with {}'.format(values))
            FieldTrial.create_fieldTrial(**values)
        else:
            print('-- Rejecting {}'.format(filename))
        return anyFound


# def discoverTrials():
#     dirList = [
#             '/Volumes/marketing/EXTERNO BMOVE/ENSAYOS BIOFERTILIZANTES',
#             '/Volumes/marketing/EXTERNO BMOVE/ENSAYOS FUN BIOLOGICOS',
#             '/Volumes/marketing/EXTERNO BMOVE/FERTILIZANTES',
#             '/Volumes/marketing/EXTERNO BMOVE/ENSAYOS',
#             '/Volumes/registro/REGISTROS nuevo ANEJO II-III',
#             '/Volumes/marketing/EXTERNO BMOVE/ENSAYOS AGROBIOTECNOLÓGICOS']
#     basedir = '/Users/jsantiago/Documents/estudios/'
#     scanner = ReportFinder(basedir)
#     scanner.discover(dirList, importer=True)


# def importTrials():
#     basedir = '/Users/jsantiago/Documents/estudios/'
#     scanner = ReportFinder(basedir)
#     scanner.importer()


# if __name__ == "__main__":
#     discoverTrials()
    # importTrials()
