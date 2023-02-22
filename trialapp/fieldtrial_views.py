# Create your views here.
import django_filters

from django_filters.views import FilterView
from django.urls import reverse_lazy
from django.contrib.auth.mixins import LoginRequiredMixin
# from rest_framework import permissions
from django.contrib.auth.decorators import login_required
from trialapp.models import Evaluation, FieldTrial, Thesis,\
                            TrialAssessmentSet
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
            '-initiation_date', 'objective', 'product', 'crop', 'plague')
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
            {'name': 'Location',
             'value': self.showValue(fieldTrial.location)}
        ]]

    def get(self, request, *args, **kwargs):
        template_name = 'trialapp/fieldtrial_show.html'
        field_trial_id = kwargs.get('field_trial_id', None)
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
                        css_class="card no-border"),
                    css_class='col-md-4'),
                Div(Div(HTML('Status'), css_class="card-header-baas h4"),
                    Div(Div(Field('trial_type', css_class='mb-2'),
                            Field('trial_status', css_class='mb-2'),
                            Field('responsible', css_class='mb-2'),
                            Field('initiation_date', css_class='mb-2'),
                            Field('completion_date', css_class='mb-2'),
                            css_class="card-body-baas"),
                        css_class="card no-border"),
                    Div(HTML('Assessments'), css_class="card-header-baas h4"),
                    Div(Div(Field('ref_to_eppo', css_class='mb-2'),
                            Field('ref_to_criteria', css_class='mb-2'),
                            Field('comments_criteria', css_class='mb-2'),
                            css_class="card-body-baas"),
                        css_class="card no-border"),
                    css_class='col-md-4'),
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
                                css_class='mb-2'),
                            Field('contact', css_class='mb-2'),
                            Field('cro', css_class='mb-2'),
                            Field('location', css_class='mb-2'),
                            css_class="card-body-baas"),
                        css_class="card no-border"),
                    css_class='col-md-4'))))


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
            'lenght_row', 'net_surface', 'gross_surface', 'code')

    def __init__(self, *args, **kwargs):
        super(FieldTrialForm, self).__init__(*args, **kwargs)
        self.fields['trial_type'].label = 'Type'
        self.fields['trial_status'].label = 'Status'
        self.fields['cro'].required = False
        self.fields['description'].widget = forms.Textarea(attrs={'rows': 10})
        self.fields['description'].required = False
        self.fields['ref_to_eppo'].label = "EPPO Reference"
        self.fields['ref_to_eppo'].required = False
        self.fields['ref_to_criteria'].label = "Criteria Reference"
        self.fields['ref_to_criteria'].required = False
        self.fields['comments_criteria'].label = "Criteria comments"
        self.fields['comments_criteria'].required = False
        self.fields['comments_criteria'].widget = forms.Textarea(
            attrs={'rows': 5})
        self.fields['plague'].required = False
        self.fields['initiation_date'].widget = MyDateInput()
        self.fields['completion_date'].widget = MyDateInput()
        self.fields['completion_date'].required = False
        self.fields['blocks'].label = "# blocks"
        self.fields['blocks'].widget = forms.NumberInput()

        self.fields['replicas_per_thesis'].label = "# replicas"
        self.fields['replicas_per_thesis'].widget = forms.NumberInput()

        self.fields['samples_per_replica'].label = "# samples"
        self.fields['samples_per_replica'].widget = forms.NumberInput()
        self.fields['samples_per_replica'].required = False

        self.fields['distance_between_plants'].label = "Plants separation"
        self.fields['distance_between_plants'].required = False

        self.fields['distance_between_rows'].label = "Rows separation"
        self.fields['distance_between_rows'].required = False

        self.fields['number_rows'].label = "# rows"
        self.fields['number_rows'].required = False

        self.fields['lenght_row'].label = "Row length (m)"
        self.fields['lenght_row'].required = False

        self.fields['net_surface'].label = "Net area plot (m2)"
        self.fields['net_surface'].required = False

        self.fields['gross_surface'].label = "Gross area plot (m2)"
        self.fields['gross_surface'].required = False


class FieldTrialCreateView(LoginRequiredMixin, CreateView):
    model = FieldTrial
    form_class = FieldTrialForm
    template_name = 'baaswebapp/model_edit_form.html'

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
    template_name = 'baaswebapp/model_edit_form.html'

    def get_form(self, form_class=FieldTrialForm):
        form = super().get_form(form_class)
        form.helper = FieldTrialFormLayout(new=False)
        return form


class FieldTrialDeleteView(DeleteView):
    model = FieldTrial
    success_url = reverse_lazy('fieldtrial-list')
    template_name = 'trialapp/fieldtrial_delete.html'
