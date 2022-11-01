from math import ceil
import random
from trialapp.models import Replica, Thesis


class LayoutTrial:

    @classmethod
    def calculateLayoutDim(cls, fieldTrial, numberThesis):
        rows = fieldTrial.rows_layout
        numberReplicas = fieldTrial.replicas_per_thesis
        return rows, ceil(numberThesis * numberReplicas / rows)

    @classmethod
    def computeInitialLayout(cls, fieldTrial, numberThesis):
        deck = []
        rows, columns = LayoutTrial.calculateLayoutDim(
            fieldTrial, numberThesis)
        for i in range(0, rows):
            deck.append([None for j in range(0, columns)])
        return deck, (rows, columns)

    @classmethod
    def showLayout(cls, fieldTrial, thesisTrial):
        rows, columns = LayoutTrial.calculateLayoutDim(
            fieldTrial, len(thesisTrial))
        deck = [[None for i in range(0, columns)] for i in range(0, rows)]

        # Place the thesis in the deck
        for thesis in thesisTrial:
            for replica in Replica.getObjects(thesis):
                if (replica.pos_x == 0) or (replica.pos_y == 0):
                    continue
                deck[replica.pos_x-1][replica.pos_y-1] = replica.getShortName()
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
    def isSameThesis(cls, deckItem: Replica, item: Replica):
        if deckItem is None:
            return False
        return True if deckItem.thesis.id == item.thesis.id else False

    @classmethod
    def tryAssign(cls, deck, row, column, item: Replica):
        if item is None:
            return False
        print('{},{} [{}]'.format(row, column, item.thesis.id))
        p_x = LayoutTrial.rangeToExplore(row)
        p_y = LayoutTrial.rangeToExplore(column)
        print('p_x is {}'.format(p_x))
        print('p_y is {}'.format(p_y))
        if p_x is not None and\
           LayoutTrial.isSameThesis(deck[p_x][column], item):
            print('ARRIBA')
            return False
        if p_y is not None and LayoutTrial.isSameThesis(deck[row][p_y], item):
            print('IZQUIERDA')
            return False
        item.pos_x = row+1
        item.pos_y = column+1
        deck[row][column] = item
        item.save()
        return True

    @classmethod
    def assignReplica(cls, toBeAssigned, deck, row, column,
                      number_tries=3):
        item = LayoutTrial.randomChooseItem(toBeAssigned)
        if item is None:
            return False
        tried = 0
        while tried < number_tries:
            if LayoutTrial.tryAssign(deck, row, column, item):
                return True
            tried += 1
        return False

    @classmethod
    def distributeLayout(cls, fieldTrial, thesisTrial):
        deck, (rows, columns) = LayoutTrial.computeInitialLayout(
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
        for row in range(0, rows):
            for column in range(0, columns):
                if LayoutTrial.assignReplica(toBeAssigned, deck, row, column):
                    assignedReplicas += 1
                if len(toBeAssigned) == 0:
                    return deck
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
