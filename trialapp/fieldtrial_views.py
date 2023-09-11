import datetime
from django.db.models import Q
from django.urls import reverse_lazy
from django import forms
from django.http import HttpResponseRedirect, FileResponse
from django.contrib.auth.mixins import LoginRequiredMixin
import django_filters
from django_filters.views import FilterView
from django.views.generic.edit import CreateView, UpdateView, DeleteView
from django.views.generic import DetailView
from crispy_forms.helper import FormHelper
from crispy_forms.layout import Layout, Div, Submit, Field, HTML, Row
from crispy_forms.bootstrap import FormActions
from trialapp.models import FieldTrial, Objective, \
    Product, TrialStatus, TrialType, Crop, Plague
from trialapp.trial_helper import TrialFile, TrialModel, \
    PdfTrial, TrialPermission
from trialapp.trial_views import TrialContent
from django.core.paginator import Paginator
from django.utils.translation import gettext_lazy as _


class FieldTrialFilter(django_filters.FilterSet):
    name = django_filters.CharFilter(lookup_expr='icontains')
    trial_status = django_filters.ModelChoiceFilter(
        queryset=TrialStatus.objects.all().order_by('name'),
        empty_label="Status")
    trial_type = django_filters.ModelChoiceFilter(
        queryset=TrialType.objects.all().order_by('name'),
        empty_label="Type")
    objective = django_filters.ModelChoiceFilter(
        queryset=Objective.objects.all().order_by('name'),
        empty_label="Objective")
    crop = django_filters.ModelChoiceFilter(
        queryset=Crop.objects.all().order_by('name'),
        empty_label="Crop")
    product = django_filters.ModelChoiceFilter(
        queryset=Product.objects.all().order_by('name'),
        empty_label="Product")
    plague = django_filters.ModelChoiceFilter(
        queryset=Plague.objects.all().order_by('name'),
        empty_label="Plague")

    class Meta:
        model = FieldTrial
        fields = ['name', 'trial_status', 'trial_type', 'objective', 'product',
                  'crop', 'plague']


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

    def getList(self, filter):
        objectList = FieldTrial.objects.filter(filter).order_by(
            '-code', 'name')

        new_list = []
        for item in objectList:
            new_list.append(
                TrialContent(item.id, TrialContent.ONLY_TRIAL_DATA,
                             trial=item).showInTrialList())
        return new_list

    def get_context_data(self, **kwargs):
        resultPerPage = 5
        if self.request.GET.get('page'):
            page = self.request.GET.get('page')
        else:
            page = 1

        paramsReplyTemplate = FieldTrialFilter.Meta.fields
        q_objects = Q(trial_meta=FieldTrial.TrialMeta.FIELD_TRIAL)
        for paramIdName in paramsReplyTemplate:
            paramId = self.getAttrValue(paramIdName)
            if paramIdName == 'name' and paramId:
                q_name = Q()
                q_name |= Q(name__icontains=paramId)
                q_name |= Q(responsible__icontains=paramId)
                q_name |= Q(code__icontains=paramId)
                q_objects &= q_name
            elif paramId:
                q_objects &= Q(**({'{}__id'.format(paramIdName): paramId}))
        new_list = []
        orderBy = paramsReplyTemplate.copy()
        orderBy.append('name')
        filter = FieldTrialFilter(self.request.GET)
        new_list = self.getList(q_objects)

        paginator = Paginator(new_list, resultPerPage)

        return {'object_list': paginator.get_page(page).object_list,
                'titleList': '({}) Field trials'.format(len(new_list)),
                'add_url': 'fieldtrial-add',
                'filter': filter,
                'paginator': paginator,
                'page': paginator.get_page(page)}


class FieldTrialApi(LoginRequiredMixin, DetailView):
    model = FieldTrial
    template_name = 'trialapp/fieldtrial_show.html'
    context_object_name = 'fieldTrial'

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        fieldTrial = self.get_object()
        # Add additional data to the context
        trialPermision = TrialPermission(fieldTrial,
                                         self.request.user).getPermisions()

        dataTrial = TrialModel.prepareDataItems(fieldTrial)

        showData = {
            'fieldTrial': fieldTrial, 'titleView': fieldTrial.code,
            'dataTrial': dataTrial}

        return {**context, **showData, **trialPermision}


class FieldTrialFormLayout(FormHelper):

    def showGoal(self):
        return Div(
            Div(HTML('Goal'), css_class="card-header-baas-trial"),
            Div(Row(Div(Field('objective', css_class='trial-input'),
                        Field('product', css_class='trial-input'),
                        css_class='col-md-6'),
                    Div(Field('crop', css_class='trial-input'),
                        Field('plague', css_class='trial-input'),
                        css_class='col-md-6'),
                    css_class=''),
                css_class="m-3"),
            css_class="card no-border mb-3")

    def showStatus(self):
        return Div(
            Div(HTML('Status'), css_class="card-header-baas-trial"),
            Div(Row(Div(Field('trial_type', css_class='trial-input'),
                        Field('initiation_date', css_class='trial-input'),
                        Field('public', css_class='trial-input'),
                        css_class='col-md-6'),
                    Div(Field('trial_status', css_class='trial-input'),
                        Field('completion_date', css_class='trial-input'),
                        Field('favorable', css_class='trial-input'),
                        Field('responsible', css_class='trial-input'),
                        css_class='col-md-6'),
                    css_class=''),
                css_class="m-3"),
            css_class="card no-border mb-3")

    def showAssessments(self):
        return Div(
            Div(HTML('Assessments'), css_class="card-header-baas-trial"),
            Div(Row(Div(Field('ref_to_eppo', css_class='trial-input'),
                        css_class='col-md-6'),
                    Div(Field('ref_to_criteria', css_class='trial-input'),
                        css_class='col-md-6')),
                css_class="m-3"),
            css_class="card no-border mb-3")

    def showLocation(self):
        return Div(
            Div(HTML('Location'), css_class="card-header-baas-trial"),
            Div(Field('contact', css_class='trial-input'),
                Field('cro', css_class='trial-input'),
                Field('location', css_class='trial-input'),
                Field('latitude', css_class='trial-input'),
                Field('longitude', css_class='trial-input'),
                css_class="m-3"),
            css_class="card no-border mb-3")

    def showApplications(self):
        return Div(
            Div(HTML('Applications'), css_class="card-header-baas-trial"),
            Div(Row(Div(Field('application_volume', css_class='trial-input'),
                        css_class='col-md-3'),
                    Div(Field('application_volume_unit',
                              css_class='trial-input'),
                        css_class='col-md-3'),
                    Div(Field('mode', css_class='trial-input'),
                        css_class='col-md-6')),
                css_class="m-3"),
            css_class="card no-border mb-3")

    def showHeader(self, title, submitTxt):
        return Row(
            Div(HTML(title), css_class='col-md-1 txt-encode-25-700'),
            Div(Field('code', css_class='trial-input'), css_class='col-md-2'),
            Div(Field('name', css_class='trial-input'), css_class='col-md-7'),
            Div(FormActions(
                Submit('submit', submitTxt, css_class="btn btn-info")),
                css_class='col-md-1 text-sm-end'),
            css_class='mt-3 mb-3')

    def showReportInfo(self):
        return Div(
            Div(HTML('Report'), css_class="card-header-baas-trial"),
            Div(Field('description', css_class='trial-input'),
                Field('comments_criteria', css_class='trial-input'),
                Field('conclusion', css_class='trial-input'),
                css_class="m-3"),
            css_class="card no-border mb-3")

    def showLayout(self):
        return Div(
            Div(HTML('Layout'), css_class="card-header-baas-trial"),
            Div(Row(Div(Field('blocks', css_class='trial-input'),
                        Field('replicas_per_thesis',
                              css_class='trial-input'),
                        Field('samples_per_replica',
                              css_class='trial-input'),
                        Field('number_rows', css_class='trial-input'),
                        css_class='col-md-6'),
                    Div(Field('gross_surface', css_class='trial-input'),
                        Field('net_surface', css_class='trial-input'),
                        Field('lenght_row', css_class='trial-input'),
                        Field('distance_between_rows',
                              css_class='trial-input'),
                        Field('distance_between_plants',
                              css_class='trial-input'),
                        css_class='col-md-6'),
                    css_class=''),
                css_class="m-3"),
            css_class="card no-border mb-3")

    def showCultive(self):
        return Div(
            Div(HTML('Cultive'), css_class="card-header-baas-trial"),
            Div(Row(Div(Field('crop_variety', css_class='trial-input'),
                        Field('irrigation', css_class='trial-input'),
                        Field('seed_date', css_class='trial-input'),
                        css_class='col-md-6'),
                    Div(Field('cultivation', css_class='trial-input'),
                        Field('soil', css_class='trial-input'),
                        Field('crop_age', css_class='trial-input'),
                        Field('transplant_date', css_class='trial-input'),
                        css_class='col-md-6'),
                    css_class=''),
                css_class="m-3"),
            css_class="card no-border mb-3")

    def __init__(self, new=True):
        super().__init__()
        title = 'New' if new else 'Edit'
        submitTxt = 'Create' if new else 'Save'
        self.add_layout(Layout(
            self.showHeader(title, submitTxt),
            Row(
                Div(self.showGoal(),
                    self.showStatus(),
                    self.showLocation(),
                    css_class="col-md-4"),
                Div(self.showLayout(),
                    self.showCultive(),
                    css_class="col-md-3"),
                Div(self.showAssessments(),
                    self.showApplications(),
                    self.showReportInfo(),
                    css_class="col-md-5"),
                )))


class FieldTrialForm(forms.ModelForm):
    class Meta:
        model = FieldTrial
        fields = TrialModel.FIELD_TRIAL_FIELDS

    def __init__(self, *args, **kwargs):
        super(FieldTrialForm, self).__init__(*args, **kwargs)
        TrialModel.applyModel(self)


class FieldTrialCreateView(LoginRequiredMixin, CreateView):
    model = FieldTrial
    form_class = FieldTrialForm
    template_name = 'baaswebapp/model_edit_full.html'

    def get_form(self, form_class=FieldTrialForm):
        form = super().get_form(form_class)
        form.helper = FieldTrialFormLayout()
        form.fields['code'].initial = FieldTrial.getCode(
            datetime.date.today(), True)
        form.fields['responsible'].initial = self.request.user.get_username()
        form.fields['trial_status'].initial = TrialStatus.objects.get(
            name=TrialStatus.OPEN).id
        return form

    def form_valid(self, form):
        if form.is_valid():
            fieldTrial = form.instance
            fieldTrial.code = FieldTrial.getCode(datetime.date.today(), True)
            fieldTrial.trial_meta = FieldTrial.TrialMeta.FIELD_TRIAL
            fieldTrial.save()
            TrialFile().createTrialFolder(fieldTrial.code)
            return HttpResponseRedirect(fieldTrial.get_absolute_url())


class FieldTrialUpdateView(LoginRequiredMixin, UpdateView):
    model = FieldTrial
    form_class = FieldTrialForm
    template_name = 'baaswebapp/model_edit_full.html'

    def get_form(self, form_class=FieldTrialForm):
        form = super().get_form(form_class)
        form.helper = FieldTrialFormLayout(new=False)
        return form


class FieldTrialDeleteView(LoginRequiredMixin, DeleteView):
    model = FieldTrial
    success_url = reverse_lazy('fieldtrial-list')
    template_name = 'trialapp/fieldtrial_delete.html'


class DownloadTrial(LoginRequiredMixin, DetailView):
    model = FieldTrial

    def get(self, request, *args, **kwargs):
        trial = self.get_object()
        trialP = TrialPermission(trial, self.request.user)
        error = None
        if trialP.canDownload():
            error = _('Fail on generating download')
            try:
                exportFile = PdfTrial(trial, useBuffer=True)
                exportFile.produce()
                # Create a FileResponse with the PDF file and appropriate
                # content type
                response = FileResponse(exportFile.getBuffer(),
                                        as_attachment=True,
                                        filename=exportFile.getName())
                return response
            except ValueError:
                pass
        else:
            return trialP.renderError(request, error=error)
