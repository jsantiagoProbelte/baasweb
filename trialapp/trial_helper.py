from math import ceil
import random
from trialapp.models import FieldTrial, Replica, Thesis,\
                            Evaluation


class LayoutTrial:

    @classmethod
    def calculateLayoutDim(cls, fieldTrial, numberThesis):
        blocks = fieldTrial.blocks
        numberReplicas = fieldTrial.replicas_per_thesis
        rows = 0 if blocks == 0 else\
            ceil(numberThesis * numberReplicas / blocks)
        return rows, blocks

    @classmethod
    def computeInitialLayout(cls, fieldTrial, numberThesis):
        rows, blocks = LayoutTrial.calculateLayoutDim(
            fieldTrial, numberThesis)
        deck = [[LayoutTrial.setDeckCell(None, None)
                 for i in range(0, blocks)] for i in range(0, rows)]
        return deck, (rows, blocks)

    @classmethod
    def setDeckCell(cls, replica: Replica, evaluation):
        if replica is None:
            return {'name': 'None',
                    'replica_id': 0,
                    'number': 0}
        else:
            return {'name': replica.getShortName(),
                    'replica_id': replica.id,
                    'number': replica.thesis.number,
                    'id': replica.generateReplicaDataSetId(evaluation)}

    @classmethod
    def showLayout(cls, fieldTrial: FieldTrial,
                   evaluation: Evaluation, thesisTrial):
        deck, (rows, columns) = LayoutTrial.computeInitialLayout(
            fieldTrial, len(thesisTrial))
        # Place the thesis in the deck
        for thesis in thesisTrial:
            for replica in Replica.getObjects(thesis):
                if (replica.pos_x > 0) and (replica.pos_y > 0) and\
                   (replica.pos_x <= rows) and (replica.pos_y <= columns):
                    deck[replica.pos_x-1][replica.pos_y-1] =\
                        LayoutTrial.setDeckCell(replica, evaluation)
        return deck

    @classmethod
    def rangeToExplore(cls, current):
        return current - 1 if current > 0 else None

    @classmethod
    def isSameThesis(cls, deckItem, item: Replica):
        if deckItem is None:
            return False
        return True if deckItem['number'] == item.thesis.number else False

    @classmethod
    def assignCell(cls, deck, item, row, column):
        item.pos_x = row+1
        item.pos_y = column+1
        deck[row][column] = LayoutTrial.setDeckCell(item, None)
        item.save()

    @classmethod
    def tryAssign(cls, deck, row, column, item: Replica):
        if item is None:
            return False
        # Check if it is free
        if deck[row][column]['replica_id'] != 0:
            return False

        p_x = LayoutTrial.rangeToExplore(row)
        p_y = LayoutTrial.rangeToExplore(column)
        if p_x is not None and\
           LayoutTrial.isSameThesis(deck[p_x][column], item):
            return False
        if p_y is not None and LayoutTrial.isSameThesis(deck[row][p_y], item):
            return False
        LayoutTrial.assignCell(deck, item, row, column)
        return True

    @classmethod
    def shuffleAndAssigned(cls, deck, toBeAssigned, rows, columns):
        random.shuffle(toBeAssigned)
        row = 0
        column = 0
        failedAttempts = []
        while len(toBeAssigned) > 0:
            replica = toBeAssigned.pop()
            replica.pos_x = 0
            replica.pos_y = 0
            replica.save()
            success = LayoutTrial.tryAssign(deck, row, column, replica)
            if success:
                column = column+1
                if column >= columns:
                    column = 0
                    row = row+1
                    if row >= rows:
                        # TODO: we reach the limit of the deck
                        break
            else:
                failedAttempts.append(replica)
        for item in failedAttempts:
            LayoutTrial.assignCell(deck, item, row, column)
            column = column+1
            if column >= columns:
                column = 0
                row = row+1
                if row >= rows:
                    # TODO: we reach the limit of the deck
                    break
        return deck

    @classmethod
    def distributeLayout(cls, fieldTrial):
        thesisTrial = Thesis.getObjects(fieldTrial)
        numT = len(thesisTrial)
        if (numT == 0) or (fieldTrial.blocks == 0) or\
           (fieldTrial.replicas_per_thesis == 0):
            return None
        deck, (rows, columns) = LayoutTrial.computeInitialLayout(
            fieldTrial, numT)
        foundReplicas = 0
        toBeAssignedLists = [[] for i in range(0, rows+1)]
        # Make a vector with all replicas thesis
        for thesis in thesisTrial:
            i = 0
            for replica in Replica.getObjects(thesis):
                toBeAssignedLists[i].append(replica)
                i = i+1 if i < rows else 0
                foundReplicas += 1
        toBeAssigned = []
        for j in range(0, foundReplicas):
            for i in range(0, rows+1):
                if len(toBeAssignedLists[i]) > 0:
                    toBeAssigned.append(toBeAssignedLists[i].pop())
        # Assigned each cell of the deck
        return LayoutTrial.shuffleAndAssigned(deck, toBeAssigned,
                                              rows, columns)


class FactoryTrials:
    @classmethod
    def createThesisReplicasLayout(cls, request, values, fieldTrial):
        # This is a new field trial
        thesis = Thesis.create_Thesis(
            name=Thesis.getValueFromRequestOrArray(
                request, values, 'name'),
            number=Thesis.getValueFromRequestOrArray(
                request, values, 'number'),
            field_trial_id=fieldTrial.id,
            description=Thesis.getValueFromRequestOrArray(
                request, values, 'description'),
            number_applications=Thesis.getValueFromRequestOrArray(
                request, values, 'number_applications', intValue=True),
            interval=Thesis.getValueFromRequestOrArray(
                request, values, 'interval', intValue=True),
            first_application=Thesis.getValueFromRequestOrArray(
                request, values, 'first_application', returnNoneIfEmpty=True),
            mode=Thesis.getValueFromRequestOrArray(
                request, values, 'mode', returnNoneIfEmpty=True))
        Replica.createReplicas(thesis, fieldTrial.replicas_per_thesis)

        # Reassigned all replicas of the same
        LayoutTrial.distributeLayout(fieldTrial)
        return thesis
