from math import ceil
import random
from trialapp.models import FieldTrial, Replica, Thesis,\
                            Evaluation


class LayoutTrial:

    @classmethod
    def calculateLayoutDim(cls, fieldTrial, numberThesis):
        blocks = fieldTrial.blocks
        numberReplicas = fieldTrial.replicas_per_thesis
        return ceil(numberThesis * numberReplicas / blocks), blocks

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
        deck, (blocks, columns) = LayoutTrial.computeInitialLayout(
            fieldTrial, len(thesisTrial))
        # Place the thesis in the deck
        for thesis in thesisTrial:
            for replica in Replica.getObjects(thesis):
                if (replica.pos_x == 0) or (replica.pos_y == 0):
                    continue
                deck[replica.pos_x-1][replica.pos_y-1] =\
                    LayoutTrial.setDeckCell(replica, evaluation)
        return deck

    @classmethod
    def randomChooseItem(cls, toBeAssigned):
        lenghtList = len(toBeAssigned)
        if lenghtList == 0:
            return None
        # randowm pick one
        position = random.randrange(lenghtList)
        # pop it from the vector
        return toBeAssigned.pop(position)

    @classmethod
    def rangeToExplore(cls, current):
        return current - 1 if current > 0 else None

    @classmethod
    def isSameThesis(cls, deckItem, item: Replica):
        if deckItem is None:
            return False
        return True if deckItem['number'] == item.thesis.number else False

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
        item.pos_x = row+1
        item.pos_y = column+1
        deck[row][column] = LayoutTrial.setDeckCell(item, None)
        item.save()
        return True

    @classmethod
    def distributeLayout(cls, fieldTrial, thesisTrial):
        deck, (blocks, columns) = LayoutTrial.computeInitialLayout(
            fieldTrial, len(thesisTrial))
        foundReplicas = 0
        assignedReplicas = 0

        toBeAssigned = []
        # Make a vector with all replicas thesis
        for thesis in thesisTrial:
            for replica in Replica.getObjects(thesis):
                toBeAssigned.append(replica)
                foundReplicas += 1

        # Assigned each cell of the deck
        for replica in toBeAssigned:
            assigned = False
            for column in range(0, columns):
                for row in range(0, blocks):
                    if LayoutTrial.tryAssign(deck,
                                             row, column, replica):
                        assigned = True
                        assignedReplicas += 1
                        break
                if assigned:
                    break
        return deck


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
                request, values, 'description'))
        Replica.createReplicas(thesis, fieldTrial.replicas_per_thesis)

        # Reassigned all replicas of the same
        LayoutTrial.distributeLayout(fieldTrial,
                                     Thesis.getObjects(fieldTrial))
        return thesis
