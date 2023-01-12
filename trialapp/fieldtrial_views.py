# Create your views here.
import django_filters
from django_filters.views import FilterView
from django.contrib.auth.mixins import LoginRequiredMixin
# from rest_framework import permissions
from django.contrib.auth.decorators import login_required
from trialapp.models import Evaluation, FieldTrial, Thesis,\
                            TrialAssessmentSet
from django.shortcuts import render, get_object_or_404, redirect
from .forms import FieldTrialCreateForm
from trialapp.trial_helper import LayoutTrial
from rest_framework.views import APIView
from rest_framework.response import Response
import datetime


class FieldTrialFilter(django_filters.FilterSet):
    class Meta:
        model = FieldTrial
        fields = ['objective', 'product', 'crop', 'plague']


class FieldTrialListView(LoginRequiredMixin, FilterView):
    model = FieldTrial
    paginate_by = 100  # if pagination is desired
    login_url = '/login'
    filterset_class = FieldTrialFilter
    template_name = 'trialapp/fieldtrial_list.html'

    def getAttrValue(self, label):
        if label in self.request.GET:
            if self.request.GET[label] != '':
                return self.request.GET[label]
        return None

    def get_context_data(self, **kwargs):
        filter_kwargs = {}
        paramsReplyTemplate = FieldTrialFilter.Meta.fields
        for paramIdName in paramsReplyTemplate:
            paramId = self.getAttrValue(paramIdName)
            if paramId:
                filter_kwargs['{}__id'.format(paramIdName)] = paramId
        new_list = []
        orderBy = paramsReplyTemplate.copy()
        orderBy.append('name')
        objectList = FieldTrial.objects.filter(
            **filter_kwargs).order_by(
            '-created', 'objective', 'product', 'crop', 'plague')
        filter = FieldTrialFilter(self.request.GET)
        for item in objectList:
            evaluations = Evaluation.objects.filter(field_trial=item).count()
            thesis = Thesis.objects.filter(field_trial=item).count()
            results = TrialAssessmentSet.objects.\
                filter(field_trial=item).count()
            new_list.append({
                'code': item.code,
                'name': item.name,
                'crop': item.crop.name,
                'product': item.product.name,
                'trial_status': item.trial_status if item.trial_status else '',
                'project': item.project.name,
                'objective': item.objective.name,
                'plague': item.plague.name if item.plague else '',
                'id': item.id,
                'results': results,
                'evaluations': evaluations,
                'thesis': thesis})
        return {'object_list': new_list,
                'titleList': '({}) Field trials'.format(len(objectList)),
                'filter': filter}


@login_required
def editNewFieldTrial(request, field_trial_id=None, errors=None):
    initialValues = {
        'field_trial_id': None,
        'code': FieldTrial.getCode(datetime.date.today(), True)}
    template_name = 'trialapp/fieldtrial_edit.html'
    title = 'New'
    if field_trial_id is not None:
        title = 'Edit'
        fieldTrial = get_object_or_404(FieldTrial, pk=field_trial_id)
        initialValues = {
            'field_trial_id': fieldTrial.id,
            'code': fieldTrial.code,
            'name': fieldTrial.name,
            'trial_type': fieldTrial.trial_type.id,
            'objective': fieldTrial.objective.id,
            'responsible': fieldTrial.responsible,
            'product': fieldTrial.product.id,
            'project': fieldTrial.project.id,
            'crop': fieldTrial.crop.id,
            'plague': fieldTrial.plague.id,
            'initiation_date': fieldTrial.initiation_date,
            'completion_date': fieldTrial.completion_date,
            'contact': fieldTrial.contact,
            'cro': fieldTrial.cro,
            'location': fieldTrial.location,
            'blocks': fieldTrial.blocks,
            'replicas_per_thesis': fieldTrial.replicas_per_thesis,
            'samples_per_replica': fieldTrial.samples_per_replica,
            'distance_between_plants': fieldTrial.distance_between_plants,
            'distance_between_rows': fieldTrial.distance_between_rows,
            'number_rows': fieldTrial.number_rows,
            'lenght_row': fieldTrial.lenght_row,
            'net_surface': fieldTrial.net_surface,
            'gross_surface': fieldTrial.gross_surface
            }
    dictKwargs = FieldTrial.generateFormKwargsChoices(initialValues)
    newFieldTrial_form = FieldTrialCreateForm(**dictKwargs)
    return render(request, template_name,
                  {'create_form': newFieldTrial_form,
                   'title': title,
                   'errors': errors})


@login_required
def saveFieldTrial(request, field_trial_id=None):
    values = FieldTrial.preloadValues(request.POST)

    if 'field_trial_id' in request.POST and request.POST['field_trial_id']:
        # This is not a new user review.
        fieldTrial = get_object_or_404(FieldTrial,
                                       pk=request.POST['field_trial_id'])
        fieldTrial.name = FieldTrial.getValueFromRequestOrArray(
            request, values, 'name')
        fieldTrial.code = FieldTrial.getValueFromRequestOrArray(
            request, values, 'code')
        fieldTrial.trial_type = FieldTrial.getValueFromRequestOrArray(
            request, values, 'trial_type')
        fieldTrial.trial_status = FieldTrial.getValueFromRequestOrArray(
            request, values, 'trial_status')
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
        fieldTrial.completion_date = FieldTrial.getValueFromRequestOrArray(
            request, values, 'completion_date', returnNoneIfEmpty=True)
        fieldTrial.contact = FieldTrial.getValueFromRequestOrArray(
            request, values, 'contact')
        fieldTrial.cro = FieldTrial.getValueFromRequestOrArray(
            request, values, 'cro')
        fieldTrial.location = FieldTrial.getValueFromRequestOrArray(
            request, values, 'location')
        fieldTrial.blocks = int(FieldTrial.getValueFromRequestOrArray(
            request, values, 'blocks'))
        fieldTrial.replicas_per_thesis = FieldTrial.getValueFromRequestOrArray(
                request, values, 'replicas_per_thesis', intValue=True)
        fieldTrial.samples_per_replica = FieldTrial.getValueFromRequestOrArray(
                request, values, 'samples_per_replica', intValue=True)
        fieldTrial.distance_between_plants = FieldTrial.\
            getValueFromRequestOrArray(
                request, values, 'distance_between_plants', floatValue=True)
        fieldTrial.distance_between_rows = FieldTrial.\
            getValueFromRequestOrArray(
                request, values, 'distance_between_rows', floatValue=True)
        fieldTrial.number_rows = FieldTrial.getValueFromRequestOrArray(
                request, values, 'number_rows', intValue=True)
        fieldTrial.lenght_row = FieldTrial.getValueFromRequestOrArray(
                request, values, 'lenght_row', floatValue=True)
        fieldTrial.net_surface = FieldTrial.getValueFromRequestOrArray(
                request, values, 'net_surface', floatValue=True)
        fieldTrial.gross_surface = FieldTrial.getValueFromRequestOrArray(
                request, values, 'gross_surface', floatValue=True)
        fieldTrial.save()
        LayoutTrial.distributeLayout(fieldTrial)
    else:
        # This is a new field trial
        fieldTrial = FieldTrial.objects.create(
            name=FieldTrial.getValueFromRequestOrArray(
                request, values, 'name'),
            trial_type=FieldTrial.getValueFromRequestOrArray(
                request, values, 'trial_type'),
            trial_status=FieldTrial.getValueFromRequestOrArray(
                request, values, 'trial_status'),
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
            completion_date=FieldTrial.getValueFromRequestOrArray(
                request, values, 'completion_date', returnNoneIfEmpty=True),
            contact=FieldTrial.getValueFromRequestOrArray(
                request, values, 'contact'),
            cro=FieldTrial.getValueFromRequestOrArray(
                request, values, 'cro'),
            location=FieldTrial.getValueFromRequestOrArray(
                request, values, 'location'),
            blocks=FieldTrial.getValueFromRequestOrArray(
                request, values, 'blocks'),
            replicas_per_thesis=FieldTrial.getValueFromRequestOrArray(
                request, values, 'replicas_per_thesis'),
            samples_per_replica=FieldTrial.getValueFromRequestOrArray(
                request, values, 'samples_per_replica'),
            distance_between_plants=FieldTrial.getValueFromRequestOrArray(
                request, values, 'distance_between_plants', floatValue=True),
            distance_between_rows=FieldTrial.getValueFromRequestOrArray(
                request, values, 'distance_between_rows', floatValue=True),
            number_rows=FieldTrial.getValueFromRequestOrArray(
                request, values, 'number_rows', intValue=True),
            lenght_row=FieldTrial.getValueFromRequestOrArray(
                request, values, 'lenght_row', floatValue=True),
            net_surface=FieldTrial.getValueFromRequestOrArray(
                request, values, 'net_surface', floatValue=True),
            gross_surface=FieldTrial.getValueFromRequestOrArray(
                request, values, 'gross_surface', floatValue=True))
    return redirect('field_trial_api', field_trial_id=fieldTrial.id)


class FieldTrialApi(APIView):
    authentication_classes = []
    permission_classes = []
    http_method_names = ['delete', 'get']

    def delete(self, request, *args, **kwargs):
        item = FieldTrial.objects.get(
            pk=request.POST['item_id'])
        item.delete()

        response_data = {'msg': 'Product was deleted.'}
        return Response(response_data, status=200)

    def orderItemsInRows(self, items):
        thesisTrialRows = []
        thesisTrialRow = []
        index = 1
        for thesis in items:
            thesisTrialRow.append(thesis)
            if index % 4 == 0:
                index = 0
                thesisTrialRows.append(thesisTrialRow)
                thesisTrialRow = []
            else:
                index += 1
        if thesisTrialRow:
            thesisTrialRows.append(thesisTrialRow)
        return thesisTrialRows

    def showValue(self, value):
        return value if value else '?'

    def prepareLayoutItems(self, fieldTrial):
        return [[
            {'name': '#blocks',
             'value': self.showValue(fieldTrial.blocks)},
            {'name': '#samples/block',
             'value': self.showValue(fieldTrial.samples_per_replica)},
            {'name': '# rows',
             'value': self.showValue(fieldTrial.number_rows)},
            {'name': 'Row length (m)',
             'value': self.showValue(fieldTrial.lenght_row)},
            {'name': 'Gross area(m2)',
             'value': self.showValue(fieldTrial.gross_surface)},
            {'name': 'Farmer',
             'value': self.showValue(fieldTrial.contact)},
            {'name': 'CRO',
             'value': self.showValue(fieldTrial.cro)}
            ], [
            {'name': '#replicas',
             'value': self.showValue(fieldTrial.replicas_per_thesis)},
            {'name': 'Plants separation',
             'value': self.showValue(fieldTrial.distance_between_plants)},
            {'name': 'Rows separation',
             'value': self.showValue(fieldTrial.distance_between_rows)},
            {'name': 'Plants density (H)',
             'value': self.showValue(fieldTrial.plantDensity())},
            {'name': 'Net area (m2)',
             'value': self.showValue(fieldTrial.net_surface)},
            {'name': 'location',
             'value': self.showValue(fieldTrial.location)}
        ]]

    def get(self, request, *args, **kwargs):
        template_name = 'trialapp/fieldtrial_show.html'
        field_trial_id = None
        if 'field_trial_id' in request.GET:
            # for testing
            field_trial_id = request.GET['field_trial_id']
        elif 'field_trial_id' in kwargs:
            # from call on server
            field_trial_id = kwargs['field_trial_id']
        fieldTrial = get_object_or_404(FieldTrial, pk=field_trial_id)
        thesisTrial = Thesis.getObjects(fieldTrial)
        numberThesis = len(thesisTrial)
        assessments = Evaluation.getObjects(fieldTrial)
        trialAssessmentSets = TrialAssessmentSet.getObjects(fieldTrial)
        assessmentsData = [{'name': item.getName(),
                            'id': item.id,
                            'date': item.evaluation_date}
                           for item in assessments]

        return render(request, template_name,
                      {'fieldTrial': fieldTrial,
                       'titleView': fieldTrial.getName(),
                       'layoutData': self.prepareLayoutItems(fieldTrial),
                       'thesisTrial': thesisTrial,
                       'assessments': assessmentsData,
                       'units': trialAssessmentSets,
                       'numberThesis': numberThesis,
                       'rowsReplicas': LayoutTrial.showLayout(fieldTrial,
                                                              None,
                                                              thesisTrial)})


@login_required
def reshuffle_blocks(request, field_trial_id=None):
    fieldTrial = get_object_or_404(FieldTrial, pk=field_trial_id)
    LayoutTrial.distributeLayout(fieldTrial)
    return redirect(
        'thesis-list',
        field_trial_id=fieldTrial.id)
