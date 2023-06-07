from math import ceil
from trialapp.models import FieldTrial, Replica
from trialapp.data_models import Assessment
from baaswebapp.baas_archive import BaaSArchive


class LayoutTrial:
    @classmethod
    def calculateLayoutDim(cls, fieldTrial, numberThesis):
        blocks = fieldTrial.blocks
        numberReplicas = fieldTrial.replicas_per_thesis
        rows = 0 if blocks == 0 else\
            ceil(numberThesis * numberReplicas / blocks)
        return blocks, rows

    @classmethod
    def computeInitialLayout(cls, fieldTrial, numberThesis):
        blocks, rows = LayoutTrial.calculateLayoutDim(
            fieldTrial, numberThesis)
        deck = [[LayoutTrial.setDeckCell(None, None, x=i+1, y=j+1)
                 for i in range(0, blocks)] for j in range(0, rows)]
        return deck, (blocks, rows)

    @classmethod
    def setDeckCell(cls, replica: Replica, assessment,
                    x=0, y=0,
                    onlyThis=None):
        if replica is None:
            return {'name': '-',
                    'replica_id': 0,
                    'x': x,
                    'y': y,
                    'number': 0}
        else:
            number = replica.thesis.number
            if onlyThis and replica.thesis.id != onlyThis:
                number = 0
            return {'name': replica.getTitle(),
                    'replica_id': replica.id,
                    'number': number,
                    'x': replica.pos_x,
                    'y': replica.pos_y,
                    'id': replica.generateReplicaDataSetId(assessment)}

    @classmethod
    def headerLayout(cls, fieldTrial: FieldTrial):
        letters = ['A', 'B', 'C', 'D', 'E', 'F', 'G', 'H', 'I',
                   'J', 'K', 'L', 'M', 'N']
        header = []
        for i in range(0, fieldTrial.blocks):
            header.append({'name': letters[i],
                           'replica_id': 0,
                           'number': 0})
        return header

    @classmethod
    def showLayout(cls, fieldTrial: FieldTrial,
                   assessment: Assessment, thesisTrial,
                   onlyThis=None):
        deck, (rows, columns) = LayoutTrial.computeInitialLayout(
            fieldTrial, len(thesisTrial))
        # Place the thesis in the deck
        for thesis in thesisTrial:
            for replica in Replica.getObjects(thesis):
                if (replica.pos_x > 0) and (replica.pos_y > 0) and\
                   (replica.pos_x <= rows) and (replica.pos_y <= columns):
                    deck[replica.pos_y-1][replica.pos_x-1] =\
                        LayoutTrial.setDeckCell(
                            replica, assessment,
                            onlyThis=onlyThis)
        return deck


class TrialHelper:
    _archive = None

    def __init__(self, root_path=None, trialsFolder=None):
        self._archive = BaaSArchive(root_path=root_path,
                                    trialsFolder=trialsFolder)

    def uploadTrialFile(self, trial, filepath):
        fileBits = filepath.split('/')
        filename = fileBits[-1]
        filepath = '/'.join(fileBits[:-1])
        filepath += '/'
        self._archive.uploadFile(filename,
                                 filepath,
                                 trial.code)
        trial.report_filename = '/'.join([trial.code, filename])
        trial.save()

    def createTrialArchive(self, fieldTrialFolder):
        self._archive.createFolder(fieldTrialFolder)
