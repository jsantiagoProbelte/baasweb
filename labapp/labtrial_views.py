from django_filters.views import FilterView
from django.contrib.auth.mixins import LoginRequiredMixin
from trialapp.models import FieldTrial, Thesis, Plague, Crop, TrialStatus
from catalogue.models import Product
from trialapp.data_models import Assessment
import datetime
from django.views.generic.edit import CreateView, UpdateView
from crispy_forms.helper import FormHelper
from crispy_forms.layout import Layout, Div, Submit, Field, HTML, Row
from crispy_forms.bootstrap import FormActions
from django.http import HttpResponseRedirect
from django import forms
from trialapp.fieldtrial_views import FieldTrialFilter, TrialModel


class LabTrialListView(LoginRequiredMixin, FilterView):
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
            assessments = Assessment.objects.filter(field_trial=item).count()
            thesis = Thesis.objects.filter(field_trial=item).count()
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
                'assessments': assessments,
                'thesis': thesis})
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
                    Div(Div(Field('project', css_class='mb-2'),
                            Field('objective', css_class='mb-2'),
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
                    Div(Div(Field('blocks'),
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
        self.fields['samples_per_replica'].label = '# samples per block'


class LabTrialCreateView(LoginRequiredMixin, CreateView):
    model = FieldTrial
    form_class = LabTrialForm
    template_name = 'baaswebapp/model_edit_full.html'

    def get_form(self, form_class=LabTrialForm):
        form = super().get_form(form_class)
        form.helper = LabTrialFormLayout()
        form.fields['code'].initial = FieldTrial.getLabCode(
            datetime.date.today(), True)
        form.fields['initiation_date'].initial = datetime.date.today()
        form.fields['product'].initial = Product.getUnknown().id
        form.fields['crop'].initial = Crop.getUnknown().id
        form.fields['plague'].initial = Plague.getUnknown().id
        form.fields['blocks'].initial = 1
        form.fields['samples_per_replica'].initial = 24
        form.fields['trial_status'].initial = TrialStatus.objects.get(
            name='Open').id
        return form

    def form_valid(self, form):
        if form.is_valid():
            fieldTrial = form.instance
            fieldTrial.code = FieldTrial.getLabCode(datetime.date.today(),
                                                    True)
            fieldTrial.trial_meta = FieldTrial.TrialMeta.LAB_TRIAL
            fieldTrial.replicas_per_thesis = 1
            fieldTrial.save()
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
