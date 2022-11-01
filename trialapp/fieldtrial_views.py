# Create your views here.
from math import ceil
import random
from django.views.generic.list import ListView
# from django.contrib.auth.mixins import LoginRequiredMixin
from trialapp.models import Application, FieldTrial, Replica, Thesis
from django.shortcuts import render, get_object_or_404, redirect
from .forms import FieldTrialCreateForm

# class FieldTrialListView(LoginRequiredMixin, ListView):
#    login_url = '/login'


class FieldTrialListView(ListView):
    model = FieldTrial
    paginate_by = 100  # if pagination is desired

    def get_context_data(self, **kwargs):

        new_list = []

        for item in FieldTrial.getObjects():
            applications = Application.objects.filter(field_trial=item).count()
            thesis = Thesis.objects.filter(field_trial=item).count()

            new_list.append({
                'name': item.name,
                'crop': item.crop.name,
                'product': item.product.name,
                'project': item.project.name,
                'objective': item.objective.name,
                'plague': item.plague.name if item.plague else '',
                'id': item.id,
                'applications': applications,
                'thesis': thesis})

        return {'object_list': new_list}


def editNewFieldTrial(request, field_trial_id=None, errors=None):
    initialValues = {'field_trial_id': None}
    template_name = 'trialapp/fieldtrial_edit.html'
    title = 'New'
    if field_trial_id is not None:
        title = 'Edit'
        fieldTrial = get_object_or_404(FieldTrial, pk=field_trial_id)
        initialValues = {
            'field_trial_id': fieldTrial.id,
            'name': fieldTrial.name,
            'phase': fieldTrial.phase.id,
            'objective': fieldTrial.objective.id,
            'responsible': fieldTrial.responsible,
            'product': fieldTrial.product.id,
            'crop': fieldTrial.crop.id,
            'plague': fieldTrial.plague.id,
            'initiation_date': fieldTrial.initiation_date,
            'completion_date': fieldTrial.completion_date,
            'farmer': fieldTrial.farmer,
            'location': fieldTrial.location,
            'rows_layout': fieldTrial.rows_layout,
            'replicas_per_thesis': fieldTrial.replicas_per_thesis
            }
    elif 'name' in request.POST:
        # This is the flow in case of error
        initialValues = {
            'field_trial_id': field_trial_id,
            'name': request.POST['name'],
        }

    dictKwargs = FieldTrial.generateFormKwargsChoices(initialValues)
    newFieldTrial_form = FieldTrialCreateForm(**dictKwargs)

    return render(request, template_name,
                  {'create_form': newFieldTrial_form,
                   'title': title,
                   'errors': errors})


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


def showFieldTrial(request, field_trial_id=None, errors=None):
    template_name = 'trialapp/fieldtrial_show.html'
    fieldTrial = get_object_or_404(FieldTrial, pk=field_trial_id)
    thesisTrial = Thesis.getObjects(fieldTrial)

    return render(request, template_name,
                  {'fieldTrial': fieldTrial,
                   'thesisTrial': thesisTrial,
                   'rowsReplicas': LayoutTrial.showLayout(fieldTrial,
                                                          thesisTrial),
                   'errors': errors})


def saveFieldTrial(request, field_trial_id=None):
    values = {}
    foreignModels = FieldTrial.getForeignModels()
    for model in foreignModels:
        label = foreignModels[model]
        values[label] = model.objects.get(pk=request.POST[label])

    if 'field_trial_id' in request.POST and request.POST['field_trial_id']:
        # This is not a new user review.
        fieldTrial = get_object_or_404(FieldTrial,
                                       pk=request.POST['field_trial_id'])
        fieldTrial.name = FieldTrial.getValueFromRequestOrArray(
            request, values, 'name')
        fieldTrial.phase = FieldTrial.getValueFromRequestOrArray(
            request, values, 'phase')
        fieldTrial.objective = FieldTrial.getValueFromRequestOrArray(
            request, values, 'objective')
        fieldTrial.responsible = FieldTrial.getValueFromRequestOrArray(
            request, values, 'responsible')
        fieldTrial.product = FieldTrial.getValueFromRequestOrArray(
            request, values, 'product')
        fieldTrial.project = FieldTrial.getValueFromRequestOrArray(
            request, values, 'project')
        fieldTrial.crop = FieldTrial.getValueFromRequestOrArray(
            request, values, 'crop')
        fieldTrial.plague = FieldTrial.getValueFromRequestOrArray(
            request, values, 'plague')
        fieldTrial.initiation_date = FieldTrial.getValueFromRequestOrArray(
            request, values, 'initiation_date')
        fieldTrial.farmer = FieldTrial.getValueFromRequestOrArray(
            request, values, 'farmer')
        fieldTrial.location = FieldTrial.getValueFromRequestOrArray(
            request, values, 'location')
        fieldTrial.rows_layout = FieldTrial.getValueFromRequestOrArray(
            request, values, 'rows_layout')
        fieldTrial.replicas_per_thesis = FieldTrial.getValueFromRequestOrArray(
            request, values, 'replicas_per_thesis')
        # fieldTrial.completion_date = FieldTrial.getValueFromRequestOrArray(
        #     request, values,
        #     'completion_date')
        fieldTrial.save()

    else:
        # This is a new field trial
        fieldTrial = FieldTrial.objects.create(
            name=FieldTrial.getValueFromRequestOrArray(
                request, values, 'name'),
            phase=FieldTrial.getValueFromRequestOrArray(
                request, values, 'phase'),
            objective=FieldTrial.getValueFromRequestOrArray(
                request, values, 'objective'),
            responsible=FieldTrial.getValueFromRequestOrArray(
                request, values, 'responsible'),
            product=FieldTrial.getValueFromRequestOrArray(
                request, values, 'product'),
            project=FieldTrial.getValueFromRequestOrArray(
                request, values, 'project'),
            crop=FieldTrial.getValueFromRequestOrArray(
                request, values, 'crop'),
            plague=FieldTrial.getValueFromRequestOrArray(
                request, values, 'plague'),
            initiation_date=FieldTrial.getValueFromRequestOrArray(
                request, values, 'initiation_date'),
            farmer=FieldTrial.getValueFromRequestOrArray(
                request, values, 'farmer'),
            location=FieldTrial.getValueFromRequestOrArray(
                request, values, 'location'),
            rows_layout=FieldTrial.getValueFromRequestOrArray(
                request, values, 'rows_layout'),
            replicas_per_thesis=FieldTrial.getValueFromRequestOrArray(
                request, values, 'replicas_per_thesis')
        )

    return redirect('fieldtrial-list')
