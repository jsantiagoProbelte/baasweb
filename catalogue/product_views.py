# Create your views here.
from django_filters.views import FilterView
from django.contrib.auth.mixins import LoginRequiredMixin
from trialapp.models import Evaluation, FieldTrial, Thesis,\
                            TrialAssessmentSet, Product, ModelHelpers
from django.shortcuts import render, get_object_or_404
from trialapp.trial_helper import LayoutTrial
from rest_framework.views import APIView
from rest_framework.response import Response


class ProductListView(LoginRequiredMixin, FilterView):
    model = Product
    paginate_by = 100  # if pagination is desired
    login_url = '/login'
    template_name = 'catalogue/product_list.html'

    def getAttrValue(self, label):
        if label in self.request.GET:
            if self.request.GET[label] != '':
                return self.request.GET[label]
        return None

    def extractDistincValues(self, results, tag):
        values = {}
        for result in results:
            found = result[tag]
            if found == ModelHelpers.UNKNOWN:
                continue
            if found not in values:
                values[found] = 1
        return list(values.keys())

    def distinctValues(self, item, tag):
        results = FieldTrial.objects.filter(product=item).values(tag)
        return self.extractDistincValues(results, tag)

    def dimensionsValues(self, item):
        results = FieldTrial.objects.filter(product=item).values('id')
        ids = [value['id'] for value in results]
        tag = 'type__name'
        results = TrialAssessmentSet.objects.filter(
            field_trial_id__in=ids).values(tag)
        return self.extractDistincValues(results, tag)

    def get_context_data(self, **kwargs):
        new_list = []
        objectList = Product.getObjects()
        for item in objectList:
            fieldtrials = FieldTrial.objects.filter(product=item).count()
            crops = self.distinctValues(item, 'crop__name')
            plagues = self.distinctValues(item, 'plague__name')
            dimensions = self.dimensionsValues(item)
            new_list.append({
                'name': item.name,
                'fieldtrials': fieldtrials,
                'crops': crops,
                'plagues': plagues,
                'dimensions': dimensions,
                'id': item.id})
        return {'object_list': new_list,
                'titleList': '({}) Products'.format(len(objectList))}


class ProductApi(APIView):
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
            {'name': '#samples/block',
             'value': self.showValue(fieldTrial.samples_per_replica)},
            {'name': '# rows',
             'value': self.showValue(fieldTrial.number_rows)},
            {'name': 'Row length (m)',
             'value': self.showValue(fieldTrial.lenght_row)},
            {'name': 'Gross area plot (m2)',
             'value': self.showValue(fieldTrial.gross_surface)},
            {'name': 'Farmer',
             'value': self.showValue(fieldTrial.contact)},
            {'name': 'CRO',
             'value': self.showValue(fieldTrial.cro)}
            ], [
            {'name': 'Plants separation',
             'value': self.showValue(fieldTrial.distance_between_plants)},
            {'name': 'Rows separation',
             'value': self.showValue(fieldTrial.distance_between_rows)},
            {'name': 'Plants density (H)',
             'value': self.showValue(fieldTrial.plantDensity())},
            {'name': 'Net area plot (m2)',
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
        headerRows = LayoutTrial.headerLayout(fieldTrial)
        return render(request, template_name,
                      {'fieldTrial': fieldTrial,
                       'titleView': fieldTrial.getName(),
                       'layoutData': self.prepareLayoutItems(fieldTrial),
                       'thesisTrial': thesisTrial,
                       'assessments': assessmentsData,
                       'units': trialAssessmentSets,
                       'numberThesis': numberThesis,
                       'rowsReplicaHeader': headerRows,
                       'rowsReplicas': LayoutTrial.showLayout(fieldTrial,
                                                              None,
                                                              thesisTrial)})
