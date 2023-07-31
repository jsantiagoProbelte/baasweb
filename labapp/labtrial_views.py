from django_filters.views import FilterView
from django.contrib.auth.mixins import LoginRequiredMixin
from trialapp.models import FieldTrial, Plague, Crop, TrialStatus,\
                            Objective, TrialType
from catalogue.models import Product
from baaswebapp.models import RateTypeUnit
from labapp.models import LabDataPoint, LabThesis, LabAssessment,\
                          LabDosis
import datetime
from django.views.generic.edit import CreateView, UpdateView, DeleteView
from crispy_forms.helper import FormHelper
from crispy_forms.layout import Layout, Div, Submit, Field, HTML, Row
from crispy_forms.bootstrap import FormActions
from django.http import HttpResponseRedirect
from django import forms
from trialapp.fieldtrial_views import FieldTrialFilter
from trialapp.trial_helper import TrialModel
from trialapp.data_views import DataGraphFactory
from django.shortcuts import get_object_or_404, render
from django.urls import reverse_lazy
from rest_framework.views import APIView
from rest_framework.response import Response
from baaswebapp.graphs import GraphTrial
import numpy as np
from scipy.stats import norm
import statsmodels.api as sm


class LabTrialListView(LoginRequiredMixin, FilterView):
    model = FieldTrial
    paginate_by = 100  # if pagination is desired
    login_url = '/login'
    filterset_class = FieldTrialFilter
    template_name = 'labapp/labtrial_list.html'

    def getAttrValue(self, label):
        if label in self.request.GET:
            if self.request.GET[label] != '':
                return self.request.GET[label]
        return None

    def get_context_data(self, **kwargs):
        filter_kwargs = {'trial_meta': FieldTrial.TrialMeta.LAB_TRIAL}
        paramsReplyTemplate = FieldTrialFilter.Meta.fields
        for paramIdName in paramsReplyTemplate:
            paramId = self.getAttrValue(paramIdName)
            if paramIdName == 'name' and paramId:
                filter_kwargs['name__icontains'] = paramId
            elif paramId:
                filter_kwargs['{}__id'.format(paramIdName)] = paramId
        new_list = []
        orderBy = paramsReplyTemplate.copy()
        orderBy.append('name')
        objectList = FieldTrial.objects.filter(
            **filter_kwargs).order_by('-code', 'name')
        filter = FieldTrialFilter(self.request.GET)
        for item in objectList:
            new_list.append({
                'code': item.code,
                'name': item.name,
                'crop': item.crop.name,
                'product': item.product.name,
                'trial_status': item.trial_status if item.trial_status else '',
                'trial_type': item.trial_type.name,
                'plague': item.plague.name if item.plague else '',
                'id': item.id})
        return {'object_list': new_list,
                'add_url': 'labtrial-add',
                'titleList': '({}) Lab trials'.format(len(objectList)),
                'filter': filter}


class LabTrialFormLayout(FormHelper):
    def __init__(self, new=True):
        super().__init__()
        title = 'New' if new else 'Edit'
        submitTxt = 'Create' if new else 'Save'
        self.add_layout(Layout(
            Row(Div(HTML(title), css_class='col-md-1 h2'),
                Div(Field('code'), css_class='col-md-2'),
                Div(Field('name'), css_class='col-md-7'),
                Div(FormActions(
                        Submit('submit', submitTxt, css_class="btn btn-info")),
                    css_class='col-md-2 text-sm-end'),
                css_class='mt-3 mb-3'),
            Row(Div(Div(HTML('Goal'), css_class="card-header-baas h4"),
                    Div(Div(Field('objective', css_class='mb-2'),
                            Field('product', css_class='mb-2'),
                            Field('crop', css_class='mb-2'),
                            Field('plague', css_class='mb-2'),
                            Field('description', css_class='mb-2'),
                            css_class="card-body-baas"),
                        css_class="card no-border mb-3"),
                    css_class='col-md-4'),
                Div(Div(HTML('Status'), css_class="card-header-baas h4"),
                    Div(Div(Field('trial_type', css_class='mb-2'),
                            Field('trial_status', css_class='mb-2'),
                            Field('responsible', css_class='mb-2'),
                            Field('initiation_date', css_class='mb-2'),
                            Field('completion_date', css_class='mb-2'),
                            css_class="card-body-baas"),
                        css_class="card no-border mb-3"),
                    css_class='col-md-4'),
                Div(Div(HTML('Layout'), css_class="card-header-baas h4"),
                    Div(Div(Field('replicas_per_thesis'),
                            Field('samples_per_replica'),
                            css_class="card-body-baas"),
                        css_class="card no-border mb-3"),
                    css_class='col-md-4')
                )  # row
            ))


class LabTrialForm(forms.ModelForm):
    class Meta:
        model = FieldTrial
        fields = TrialModel.LAB_TRIAL_FIELDS

    def __init__(self, *args, **kwargs):
        super(LabTrialForm, self).__init__(*args, **kwargs)
        TrialModel.applyModel(self)
        self.fields['samples_per_replica'].label = '# samples'
        self.fields['replicas_per_thesis'].label = '# thesis'


class LabTrialCreateView(LoginRequiredMixin, CreateView):
    model = FieldTrial
    form_class = LabTrialForm
    template_name = 'baaswebapp/model_edit_full.html'

    def get_form(self, form_class=LabTrialForm):
        form = super().get_form(form_class)
        form.helper = LabTrialFormLayout()
        code = FieldTrial.getLabCode(datetime.date.today(), True)
        form.fields['code'].initial = code
        form.fields['name'].initial = code + ' Bio Trial'
        form.fields['initiation_date'].initial = datetime.date.today()
        form.fields['product'].initial = Product.getUnknown()
        form.fields['objective'].initial = Objective.getUnknown()
        form.fields['crop'].initial = Crop.getUnknown()
        form.fields['plague'].initial = Plague.getUnknown()
        form.fields['trial_type'].initial = TrialType.findOrCreate(
            name='LabTrial')
        form.fields['samples_per_replica'].initial = 24
        form.fields['trial_status'].initial = TrialStatus.objects.get(
            name=TrialStatus.OPEN).id
        form.fields['responsible'].initial = self.request.user.get_username()
        return form

    def form_valid(self, form):
        if form.is_valid():
            fieldTrial = form.instance
            fieldTrial.code = FieldTrial.getLabCode(datetime.date.today(),
                                                    True)
            fieldTrial.trial_meta = FieldTrial.TrialMeta.LAB_TRIAL
            fieldTrial.blocks = 1
            fieldTrial.save()
            # Create assessment, thesis, dosis and points
            dataHelper = DataLabHelper(fieldTrial)
            dataHelper.createData()
            return HttpResponseRedirect(fieldTrial.get_absolute_url())
        else:
            pass


class LabTrialUpdateView(LoginRequiredMixin, UpdateView):
    model = FieldTrial
    form_class = LabTrialForm
    template_name = 'baaswebapp/model_edit_full.html'

    def get_form(self, form_class=LabTrialForm):
        form = super().get_form(form_class)
        form.helper = LabTrialFormLayout(new=False)
        return form


class SetLabDataPoint(APIView):
    authentication_classes = []
    permission_classes = []
    http_method_names = ['post']

    # see generateDataPointId
    def post(self, request, format=None):
        # noqa:                      2              1
        # noqa: E501 data_point_id-[level]-[pointId]
        theIds = request.POST['data_point_id'].split('-')
        level = theIds[-2]
        pointId = theIds[-1]
        value = request.POST['data-point']
        item = LabDataPoint.objects.get(id=pointId)
        if level == DataLabHelper.T_VALUE:
            item.value = value
        if level == DataLabHelper.T_TOTAL:
            item.total = value
        item.save()
        return Response({'success': True})


class SetLabThesis(APIView):
    authentication_classes = []
    permission_classes = []
    http_method_names = ['post']

    # see generateDataPointId
    def post(self, request, format=None):
        # noqa:                      2              1
        # noqa: E501 data_point_id-[level]-[pointId]
        theIds = request.POST['data_point_id'].split('-')
        thesisId = theIds[-1]
        name = request.POST['data-point']
        thesis = LabThesis.objects.get(id=thesisId)
        thesis.name = name
        thesis.save()
        return Response({'success': True})


# Show Data methods
class DataLabHelper:
    T_VALUE = 'value'
    T_TOTAL = 'total'

    def __init__(self, trial):
        self._trial = trial

    def computeData(self):
        self._assessment = LabAssessment.objects.get(trial=self._trial)
        self._points = LabDataPoint.getDataPoints(
            self._assessment).order_by('dosis__rate', 'thesis__id')

    def prepareHeader(self, colspan=2):
        references = LabThesis.objects.filter(
            trial=self._trial).order_by('id')
        header = []
        index = 1
        for reference in references:
            header.append({
                'index': reference.getKey(),
                'color': index,
                'name': 'value',
                'colspan': colspan,
                'id': reference.id})
            header.append({
                'index': '',
                'color': index,
                'name': 'total',
                'colspan': colspan,
                'id': reference.id})
            index += 1
        return header

    def generateDataPointId(self, level, pointId=0):
        return 'data_point_id-{}-{}'.format(level, pointId)

    def prepareDataPoints(self, points):
        rows = []
        pointsRow = []
        thisDosis = 'bla'
        for point in points:
            if point.dosis.rate != thisDosis:
                if len(pointsRow) > 0:
                    rows.append({
                        'index': thisDosis,
                        'dataPoints': pointsRow})
                pointsRow = []
                thisDosis = point.dosis.rate
            pointsRow.append({
                'value': point.value,
                'item_id': self.generateDataPointId(DataLabHelper.T_VALUE,
                                                    point.id)})
            pointsRow.append({
                'value': point.total,
                'item_id': self.generateDataPointId(DataLabHelper.T_TOTAL,
                                                    point.id)})

        if len(pointsRow) > 0:
            rows.append({
                'index': thisDosis,
                'dataPoints': pointsRow})
        return rows

    def prepareAssSet(self):
        graph = 'Add data and refresh to show graph'
        rows = self.prepareDataPoints(self._points)

        # Calculate graph
        if len(self._points) > 1:
            graphHelper = DataGraphFactory(
                GraphTrial.L_DOSIS, [self._assessment],
                self._points, xAxis=GraphTrial.L_DOSIS)
            graph = graphHelper.draw()
        return rows, graph

    def showData(self):
        self.computeData()
        subtitle = 'Dilutions'
        header = self.prepareHeader()

        rows, graph = self.prepareAssSet()
        return [{
            'title': self._assessment.rate_type.getName(),
            'subtitle': subtitle,
            'header': header, 'errors': '',
            'graph': graph, 'rows': rows}]

    def createData(self):
        # Create some default data
        rateType = RateTypeUnit.findOrCreate(name='DOSIS EFFECTIVENESS',
                                             unit='NUMBER')
        assessment = LabAssessment.objects.create(
            assessment_date=datetime.date.today(),
            trial=self._trial,
            rate_type=rateType)

        thesisLab = LabThesis.createLabThesis(self._trial)
        dosisLab = LabDosis.createLabDosis()
        for thesis in thesisLab:
            for dosis in dosisLab:
                LabDataPoint.objects.create(
                    value=0.0,
                    dosis=dosis,
                    thesis=thesis,
                    assessment=assessment,
                    total=self._trial.samples_per_replica)

    def filterPercentage(self, all_percentange, all_dosis):
        filtered = []
        useValues = []
        percentageControl = 0
        for index in range(0, len(all_percentange)):
            percentage = all_percentange[index]
            if all_dosis[index] == 0:
                # This is control
                percentageControl = percentage
            if percentage > 0.3 and percentage < 0.9:
                if percentageControl > 0:
                    percentage = (percentage - percentageControl) /\
                                 (1 - percentageControl)
                filtered.append(percentage)
                useValues.append(index)
        return filtered, useValues

    def filterDosis(self, all_dosis, useValues):
        return [all_dosis[i] for i in useValues]

    def ld50(self, model):
        p1 = model.params[1]
        p0 = model.params[0]
        return 10**((-1*p0) / p1)

    def fitModelLinear(self, log_dose_levels, probits):
        y = probits
        X = sm.add_constant(log_dose_levels)
        model = sm.OLS(y, X, family=sm.families.Binomial()).fit()
        return model

    def calculateLD50(self, responses, all_doseLevels):
        log_dose_levels, probits = self.prepareSeries(
            responses,
            all_doseLevels)
        if len(log_dose_levels) == 0:
            return '', ''
        model = self.fitModelLinear(log_dose_levels, probits)
        ld50 = self.ld50(model)
        ld95 = self.calculate95(model)
        return ld50, ld95

    def prepareSeries(self, responses, all_doseLevels):
        percentanges, useValues = self.filterPercentage(
            [item[0]/item[1] for item in responses],
            all_doseLevels)
        if len(useValues) < 2:
            return [], []

        dose_levels = self.filterDosis(all_doseLevels, useValues)
        log_dose_levels = np.log10(np.array(dose_levels))
        probits = self.probit_func(np.array(percentanges))
        return log_dose_levels, probits

    def calculate95(self, model):
        z = 1.96  # the 1.96 quantile of the standard normal distribution
        p0 = model.params[0]
        p1 = model.params[1]
        ld50_probit = -p0/p1
        ld50_probit_se = model.mse_model / abs(p1)
        dev = z * ld50_probit_se

        ld50_probit_ci = (ld50_probit + dev, ld50_probit - dev)
        factor = (p0 / (p1 ** 2))

        # Transform the upper and lower bounds of the confidence interval back
        # to the original scale of the dose-response data
        ld50_ci = (ld50_probit + (factor * ld50_probit_ci[0]),
                   ld50_probit + (factor * ld50_probit_ci[1]))

        return (round(10**(ld50_ci[0]), 2), round(10**(ld50_ci[1]), 2))

    def calculateStats(self):
        data = {}
        doses = []
        for point in self._points:
            name = point.thesis.name
            if name not in data:
                data[name] = []
            value = float(point.value)
            data[name].append([value, float(point.total)])
            theDosis = float(point.dosis.rate)
            if theDosis not in doses:
                doses.append(theDosis)
        doses.sort()
        stats = {'rows': []}
        header = [thesis for thesis in data]
        header.insert(0, 'Stats')
        stats['header'] = header
        rowLD50 = ['LD50']
        row95 = ['95%']
        for thesis in data:
            responses = data[thesis]
            ld50, ld95 = self.calculateLD50(responses, doses)
            if ld50 != '':
                ld50 = round(ld50, 2)
            rowLD50.append(ld50)
            row95.append(ld95)
        stats['rows'].append(rowLD50)
        stats['rows'].append(row95)
        return stats

    def probit_func(self, values):
        probits = []
        for v in values:
            if v == 1:
                v = 0.9999
            if v == 0:
                v = 0.0001
            probits.append(norm.ppf(v))
        return probits


class LabTrialView(APIView):
    authentication_classes = []
    permission_classes = []
    http_method_names = ['get']

    def get(self, request, *args, **kwargs):
        template_name = 'labapp/labtrial_show.html'
        trial_id = kwargs.get('pk', None)
        trial = get_object_or_404(FieldTrial, pk=trial_id)
        dataTrial = TrialModel.prepareDataItems(trial)
        dataHelper = DataLabHelper(trial)
        showData = {
            'labtrial': trial, 'titleView': trial.getName(),
            'dataTrial': dataTrial,
            'allow_edit_thesis': True,
            'dataPointsForm': dataHelper.showData(),
            'stats': dataHelper.calculateStats()}
        return render(request, template_name, showData)


class LabTrialDeleteView(DeleteView):
    model = FieldTrial
    success_url = reverse_lazy('labtrial-list')
    template_name = 'labapp/labtrial_delete.html'
