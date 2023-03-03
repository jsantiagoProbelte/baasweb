# Create your views here.
import django_filters

from django_filters.views import FilterView
from django.urls import reverse_lazy
from django.contrib.auth.mixins import LoginRequiredMixin
# from rest_framework import permissions
from django.contrib.auth.decorators import login_required
from trialapp.models import\
    Evaluation, FieldTrial, Thesis, TrialAssessmentSet, Project, Objective,\
    Product, ApplicationMode, TrialStatus, TrialType, Crop, CropVariety,\
    Plague, CultivationMethod, Irrigation, Application
from django.shortcuts import render, get_object_or_404, redirect
from trialapp.trial_helper import LayoutTrial
from rest_framework.views import APIView
import datetime
from django.views.generic.edit import CreateView, UpdateView, DeleteView
from crispy_forms.helper import FormHelper
from crispy_forms.layout import Layout, Div, Submit, Field, HTML, Row
from crispy_forms.bootstrap import FormActions
from django.http import HttpResponseRedirect
from django import forms
from trialapp.forms import MyDateInput


class FieldTrialFilter(django_filters.FilterSet):

    objective = django_filters.ModelChoiceFilter(
        queryset=Objective.objects.all().order_by('name'))
    crop = django_filters.ModelChoiceFilter(
        queryset=Crop.objects.all().order_by('name'))
    product = django_filters.ModelChoiceFilter(
        queryset=Product.objects.all().order_by('name'))
    plague = django_filters.ModelChoiceFilter(
        queryset=Plague.objects.all().order_by('name'))

    class Meta:
        model = FieldTrial
        fields = ['objective', 'product', 'crop', 'plague']


class TrialModel():
    T_D = 'TypeDate'
    T_I = 'TypeInteger'
    T_N = 'TypeNoChange'
    T_T = 'TypeText'
    FIELDS = {
        'Goal': {
            'project': {'label': "Project", 'required': True, 'type': T_N,
                        'cls': Project},
            'objective': {'label': "Objective", 'required': True, 'type': T_N,
                          'cls': Objective},
            'product': {'label': "Main Product", 'required': True,
                        'type': T_N, 'cls': Product},
            'crop': {'label': "Crop", 'required': True, 'type': T_N,
                     'cls': Crop},
            'plague': {'label': "Plague", 'required': False, 'type': T_N,
                       'cls': Plague},
            'description': {'label': "Description", 'required': False,
                            'type': T_T, 'rows': 10},
        },
        'Status': {
            'trial_type': {'label': 'Type', 'required': True, 'type': T_N,
                           'cls': TrialType},
            'trial_status': {'label': 'Status', 'required': True, 'type': T_N,
                             'cls': TrialStatus},
            'responsible': {'label': 'Responsible', 'required': True,
                            'type': T_N},
            'initiation_date': {'label': 'Started', 'required': True,
                                'type': T_D},
            'completion_date': {'label': 'Completed by', 'required': False,
                                'type': T_D},
        },
        'Cultive': {
            'crop_variety': {'label': 'Crop Variety', 'required': False,
                             'type': T_N, 'cls': CropVariety},
            'cultivation': {'label': 'Cultivation Mode', 'required': False,
                            'type': T_N, 'cls': CultivationMethod},
            'irrigation': {'label': 'Irrigation', 'required': False,
                           'type': T_N, 'cls': Irrigation},
            'crop_age': {'label': 'Crop Age (years)', 'required': False,
                         'type': T_I},
            'seed_date': {'label': 'Seed date', 'required': False,
                          'type': T_D},
            'transplant_date': {'label': 'Transplante date', 'required': False,
                                'type': T_D},
        },
        'Assessments': {
            'ref_to_eppo': {'label': "EPPO Reference", 'required': False,
                            'type': T_N},
            'ref_to_criteria': {'label': "Criteria Reference",
                                'required': False, 'type': T_N},
            'comments_criteria': {'label': "Criteria comments",
                                  'required': False, 'type': T_T, 'rows': 5},
        },
        'Applications': {
            'application_volume': {'label': "Application Volume (L/Ha)",
                                   'required': False, 'type': T_N},
            'mode': {'label': "Application Mode", 'required': False,
                     'type': T_N, 'cls': ApplicationMode},
        },
        'Layout': {
            'blocks': {'label': "# blocks", 'required': True,
                       'type': T_I},
            'replicas_per_thesis': {'label': "# replicas", 'required': True,
                                    'type': T_I},
            'samples_per_replica': {'label': "# samples/replica ",
                                    'required': False, 'type': T_I},
            'distance_between_plants': {'label': "Plants separation",
                                        'required': False, 'type': T_N},
            'distance_between_rows': {'label': "Rows separation",
                                      'required': False, 'type': T_N},
            'number_rows': {'label': "# rows", 'required': False, 'type': T_I},
            'lenght_row': {'label': "Row length (m)", 'required': False,
                           'type': T_N},
            'net_surface': {'label': "Net area plot (m2)", 'required': False,
                            'type': T_N},
            'gross_surface': {'label': "Gross area plot (m2)",
                              'required': False, 'type': T_N},
        },
        'Location': {
            'contact': {'label': "Farmer", 'required': False, 'type': T_N},
            'cro': {'label': "CRO", 'required': False, 'type': T_N},
            'location': {'label': "City/Area", 'required': False, 'type': T_N},
            'latitude': {'label': "Latitude", 'required': False,
                         'type': T_N},
            'longitude': {'label': "Longitude", 'required': False,
                          'type': T_N},
        }
    }


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
            **filter_kwargs).order_by('-code', 'name')
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


class FieldTrialApi(APIView):
    authentication_classes = []
    permission_classes = []
    http_method_names = ['get']

    def prepareDataItems(self, fieldTrial):
        trialDict = fieldTrial.__dict__
        trialData = {}
        for group in TrialModel.FIELDS:
            trialData[group] = []
            for field in TrialModel.FIELDS[group]:
                label = TrialModel.FIELDS[group][field]['label']
                value = '?'
                if field in trialDict:
                    value = trialDict[field]
                else:
                    field_id = field + '_id'
                    if field_id not in trialDict:
                        continue
                    else:
                        theId = trialDict[field_id]
                        if theId is not None:
                            model = TrialModel.FIELDS[group][field]['cls']
                            value = model.objects.get(id=theId)
                showValue = value if value is not None else '?'
                trialData[group].append({'name': label, 'value': showValue})
        return trialData

    def get(self, request, *args, **kwargs):
        template_name = 'trialapp/fieldtrial_show.html'
        field_trial_id = kwargs.get('field_trial_id', None)
        fieldTrial = get_object_or_404(FieldTrial, pk=field_trial_id)
        thesisTrial = Thesis.getObjects(fieldTrial)
        numberThesis = len(thesisTrial)
        assessments = Evaluation.getObjects(fieldTrial)
        trialAssessmentSets = TrialAssessmentSet.getObjects(fieldTrial)
        dataTrial = self.prepareDataItems(fieldTrial)
        for item in assessments:
            dataTrial['Assessments'].append(
                {'name': item.getName(), 'value': item.evaluation_date})
        for item in Application.getObjects(fieldTrial):
            dataTrial['Applications'].append(
                {'name': item.getName(), 'value': item.app_date})
        headerRows = LayoutTrial.headerLayout(fieldTrial)
        return render(request, template_name,
                      {'fieldTrial': fieldTrial,
                       'titleView': fieldTrial.getName(),
                       'dataTrial': dataTrial,
                       'thesisTrial': thesisTrial,
                       'units': trialAssessmentSets,
                       'numberThesis': numberThesis,
                       'rowsReplicaHeader': headerRows,
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


class FieldTrialFormLayout(FormHelper):
    def __init__(self, new=True):
        super().__init__()
        title = 'New' if new else 'Edit'
        submitTxt = 'Create' if new else 'Save'
        self.add_layout(Layout(
            Row(Div(HTML(title),
                    css_class='col-md-1 h2'),
                Div(Field('code'),
                    css_class='col-md-2'),
                Div(Field('name'),
                    css_class='col-md-7'),
                Div(FormActions(
                        Submit('submit', submitTxt, css_class="btn btn-info")),
                    css_class='col-md-2 text-sm-end'),
                css_class='mt-3 mb-3'),
            Row(Div(Div(HTML('Goal'), css_class="card-header-baas h4"),
                    Div(Div(Field('project', css_class='mb-2'),
                            Field('objective', css_class='mb-2'),
                            Field('product', css_class='mb-2'),
                            Field('crop', css_class='mb-2'),
                            Field('plague', css_class='mb-2'),
                            Field('description', css_class='mb-2'),
                            css_class="card-body-baas"),
                        css_class="card no-border mb-3"),
                    css_class='col-md-2'),
                Div(Div(HTML('Status'), css_class="card-header-baas h4"),
                    Div(Div(Field('trial_type', css_class='mb-2'),
                            Field('trial_status', css_class='mb-2'),
                            Field('responsible', css_class='mb-2'),
                            Field('initiation_date', css_class='mb-2'),
                            Field('completion_date', css_class='mb-2'),
                            css_class="card-body-baas"),
                        css_class="card no-border mb-3"),

                    Div(HTML('Assessments'), css_class="card-header-baas h4"),
                    Div(Div(Field('ref_to_eppo', css_class='mb-2'),
                            Field('ref_to_criteria', css_class='mb-2'),
                            Field('comments_criteria', css_class='mb-2'),
                            css_class="card-body-baas"),
                        css_class="card no-border mb-3"),
                    css_class='col-md-2'),
                Div(Div(HTML('Location'), css_class="card-header-baas h4"),
                    Div(Div(Field('contact', css_class='mb-2'),
                            Field('cro', css_class='mb-2'),
                            Field('location', css_class='mb-2'),
                            Field('longitude', css_class='mb-2'),
                            Field('latitude', css_class='mb-2'),
                            css_class="card-body-baas"),
                        css_class="card no-border mb-3"),
                    Div(HTML('Applications'), css_class="card-header-baas h4"),
                    Div(Div(Field('application_volume', css_class='mb-2'),
                            Field('mode', css_class='mb-2'),
                            css_class="card-body-baas"),
                        css_class="card no-border mb-3"),
                    css_class='col-md-2'),
                Div(Div(HTML('Layout'), css_class="card-header-baas h4"),
                    Div(Div(Row(Div(Field('blocks'), css_class='col-md-4'),
                                Div(Field('replicas_per_thesis'),
                                    css_class='col-md-4'),
                                Div(Field('samples_per_replica'),
                                    css_class='col-md-4'),
                                css_class='mb-2'),
                            Row(Div(Field('number_rows'),
                                    css_class='col-md-4'),
                                Div(Field('distance_between_rows'),
                                    css_class='col-md-4'),
                                Div(Field('distance_between_plants'),
                                    css_class='col-md-4'),
                                css_class='mb-2'),
                            Row(Div(Field('lenght_row'),
                                    css_class='col-md-4'),
                                Div(Field('gross_surface'),
                                    css_class='col-md-4'),
                                Div(Field('net_surface'),
                                    css_class='col-md-4'),
                                css_class='mb-3'),
                            css_class="card-body-baas"),
                        css_class="card no-border mb-3"),
                    Div(HTML('Cultive'), css_class="card-header-baas h4"),
                    Div(Div(Row(Div(Field('crop_variety', css_class='mb-2'),
                                    Field('irrigation', css_class='mb-2'),
                                    Field('seed_date', css_class='mb-2'),
                                    css_class='col-md-6'),
                                Div(Field('cultivation', css_class='mb-2'),
                                    Field('crop_age', css_class='mb-2'),
                                    Field('transplant_date', css_class='mb-2'),
                                    css_class='col-md-6'),
                                css_class='mb-3'),
                            css_class="card-body-baas"),
                        css_class="card no-border mb-3"),
                    css_class='col-md-4')
                )  # row
            ))


class FieldTrialForm(forms.ModelForm):
    class Meta:
        model = FieldTrial
        fields = (
            'name', 'trial_type', 'objective', 'responsible', 'description',
            'ref_to_eppo', 'ref_to_criteria', 'comments_criteria', 'project',
            'product', 'crop', 'plague', 'initiation_date', 'completion_date',
            'trial_status', 'contact', 'cro', 'location', 'blocks',
            'replicas_per_thesis', 'samples_per_replica',
            'distance_between_plants', 'distance_between_rows', 'number_rows',
            'lenght_row', 'net_surface', 'gross_surface', 'code', 'irrigation',
            'application_volume', 'mode', 'crop_variety', 'cultivation',
            'crop_age', 'seed_date', 'transplant_date', 'longitude',
            'latitude')

    def __init__(self, *args, **kwargs):
        super(FieldTrialForm, self).__init__(*args, **kwargs)
        for block in TrialModel.FIELDS:
            for field in TrialModel.FIELDS[block]:
                fieldData = TrialModel.FIELDS[block][field]
                self.fields[field].label = fieldData['label']
                self.fields[field].required = fieldData['required']
                typeField = fieldData['type']
                if typeField == TrialModel.T_D:
                    self.fields[field].widget = MyDateInput()
                elif typeField == TrialModel.T_I:
                    self.fields[field].widget = forms.NumberInput()
                elif typeField == TrialModel.T_T:
                    self.fields['comments_criteria'].widget = forms.Textarea(
                        attrs={'rows': fieldData['rows']})


class FieldTrialCreateView(LoginRequiredMixin, CreateView):
    model = FieldTrial
    form_class = FieldTrialForm
    template_name = 'baaswebapp/model_edit_full.html'

    def get_form(self, form_class=FieldTrialForm):
        form = super().get_form(form_class)
        form.helper = FieldTrialFormLayout()
        form.fields['code'].initial = FieldTrial.getCode(
            datetime.date.today(), True)
        return form

    def form_valid(self, form):
        if form.is_valid():
            fieldTrial = form.instance
            fieldTrial.code = FieldTrial.getCode(datetime.date.today(), True)
            fieldTrial.save()
            return HttpResponseRedirect(fieldTrial.get_absolute_url())
        else:
            pass


class FieldTrialUpdateView(LoginRequiredMixin, UpdateView):
    model = FieldTrial
    form_class = FieldTrialForm
    template_name = 'baaswebapp/model_edit_full.html'

    def get_form(self, form_class=FieldTrialForm):
        form = super().get_form(form_class)
        form.helper = FieldTrialFormLayout(new=False)
        return form


class FieldTrialDeleteView(DeleteView):
    model = FieldTrial
    success_url = reverse_lazy('fieldtrial-list')
    template_name = 'trialapp/fieldtrial_delete.html'
