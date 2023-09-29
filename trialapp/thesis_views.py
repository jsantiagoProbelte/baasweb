# Create your views here.
from django.views.generic.list import ListView
from django.contrib.auth.mixins import LoginRequiredMixin
# from rest_framework import permissions
from trialapp.models import FieldTrial, \
    Thesis, Replica, TreatmentThesis
from django.shortcuts import get_object_or_404, redirect
from rest_framework.views import APIView
from django.shortcuts import render
from trialapp.trial_helper import LayoutTrial
from django.views.generic.edit import CreateView, UpdateView, DeleteView
from django.views.generic import DetailView, View
from django.urls import reverse
from crispy_forms.helper import FormHelper
from crispy_forms.layout import Layout, Div, Submit, Field, HTML
from crispy_forms.bootstrap import FormActions
from django.http import HttpResponseRedirect
from django import forms
from catalogue.models import Treatment, Product
from trialapp.trial_helper import TrialPermission
from trialapp.trial_views import TrialContent
from baaswebapp.models import EventBaas, EventLog


class ThesisListView(LoginRequiredMixin, ListView):
    model = Thesis
    paginate_by = 100  # if pagination is desired
    login_url = '/login'

    def getContextKeyData(self, trial):
        trialContent = TrialContent(trial.id, 'what', self.request.user)
        units, parts = trialContent.getRateTypeUnitsAndParts()
        assmts = trialContent.getAssmts()
        filterAssmts = trial.key_thesis is not None and \
            trial.control_thesis is not None and \
            trial.key_ratetypeunit is not None and \
            trial.key_ratedpart is not None
        assmtList = []
        if filterAssmts:
            for item in assmts:
                if item.part_rated == trial.key_ratedpart and \
                   item.rate_type == trial.key_ratetypeunit:
                    assmtList.append(
                        {'id': item.id, 'name': item.assessment_date})
        unitList = [{'id': item.id, 'name': item.getName()} for item in units]
        partList = [{'id': item, 'name': item} for item in parts]
        return {'trial': trial,
                'partList': partList,
                'assmtList': assmtList,
                'unitList': unitList}

    def getLayoutData(self, trial):
        allThesis, thesisDisplay = Thesis.getObjectsDisplay(trial)
        headerRows = LayoutTrial.headerLayout(trial)
        replicas = [
            {'value': item.id, 'number': item.thesis.number,
             'name': item.getTitle()}
            for item in Replica.getFieldTrialObjects(trial)]

        return {
            'thesisList': thesisDisplay,
            'rowsReplicaHeader': headerRows,
            'replicas': replicas,
            'rowsReplicas': LayoutTrial.showLayout(
                trial, None, allThesis)}

    def get_context_data(self, **kwargs):
        field_trial_id = self.kwargs['field_trial_id']
        fieldTrial = get_object_or_404(FieldTrial, pk=field_trial_id)
        permisions = TrialPermission(
            fieldTrial, self.request.user).getPermisions()
        keyContextData = self.getContextKeyData(fieldTrial)
        layoutData = self.getLayoutData(fieldTrial)
        return {
                'fieldTrial': fieldTrial,
                **layoutData,
                **keyContextData,
                **permisions}


class ThesisFormLayout(FormHelper):
    def __init__(self, new=True):
        super().__init__()
        title = 'New thesis' if new else 'Edit thesis'
        submitTxt = 'Create' if new else 'Save'
        self.add_layout(Layout(Div(
            HTML(title), css_class="h4 mt-4"),
            Div(Field('name', css_class='mb-3'),
                Field('treatment', css_class='mb-3'),
                Field('number_applications', css_class='mb-3'),
                Field('interval', css_class='mb-3'),
                Field('first_application', css_class='mb-3'),
                Field('mode', css_class='mb-3'),
                Field('description', css_class='mb-3'),
                FormActions(
                    Submit('submit', submitTxt, css_class="btn btn-info"),
                    css_class='text-sm-end'),
                css_class="card-body-baas mt-2")
            ))


class ThesisForm(forms.ModelForm):
    class Meta:
        model = Thesis
        fields = ('name', 'number_applications', 'interval', 'mode',
                  'description', 'first_application', 'treatment')

    def __init__(self, *args, **kwargs):
        super(ThesisForm, self).__init__(*args, **kwargs)
        self.fields['first_application'].required = False
        self.fields['first_application'].widget = forms.DateInput(
            format=('%Y-%m-%d'),
            attrs={'class': 'form-control',
                   'type': 'date'})
        self.fields['first_application'].show_hidden_initial = True
        self.fields['mode'].required = False
        self.fields['interval'].required = False
        self.fields['number_applications'].required = False
        self.fields['description'].required = False
        self.fields['interval'].label = 'Days between application'
        self.fields['treatment'].queryset =\
            Treatment.objects.all().order_by('batch__product_variant__product')


class ThesisCreateView(LoginRequiredMixin, CreateView):
    model = Thesis
    form_class = ThesisForm
    template_name = 'baaswebapp/model_edit_form.html'

    def get_form(self, form_class=ThesisForm):
        form = super().get_form(form_class)
        form.helper = ThesisFormLayout()
        return form

    def form_valid(self, form):
        if form.is_valid():
            form.instance.field_trial_id = self.kwargs["field_trial_id"]
            thesis = form.instance
            thesis.number = Thesis.objects.filter(
                field_trial_id=thesis.field_trial_id).count()+1
            treatment = thesis.treatment
            thesis.treatment = None
            thesis.save()

            # Take the treatment and add it to the TreatmentThesis
            TreatmentThesis.objects.create(
                treatment=treatment,
                thesis=thesis)

            EventLog.track(
                EventBaas.NEW_THESIS,
                self.request.user.id,
                thesis.field_trial_id)
            # Create replicas
            Replica.createReplicas(thesis,
                                   thesis.field_trial.replicas_per_thesis)
            return HttpResponseRedirect(self.get_success_url())

    def get_success_url(self):
        return reverse(
            'thesis-list',
            kwargs={'field_trial_id': self.kwargs["field_trial_id"]})


class ThesisFormUpdate(forms.ModelForm):
    class Meta:
        model = Thesis
        fields = ('name', 'number_applications', 'interval', 'mode',
                  'description', 'first_application')

    def __init__(self, *args, **kwargs):
        super(ThesisFormUpdate, self).__init__(*args, **kwargs)
        self.fields['first_application'].required = False
        self.fields['first_application'].widget = forms.DateInput(
            format=('%Y-%m-%d'),
            attrs={'class': 'form-control',
                   'type': 'date'})
        self.fields['first_application'].show_hidden_initial = True
        self.fields['mode'].required = False
        self.fields['interval'].required = False
        self.fields['number_applications'].required = False
        self.fields['description'].required = False
        self.fields['interval'].label = 'Days between application'


class ThesisUpdateView(LoginRequiredMixin, UpdateView):
    model = Thesis
    form_class = ThesisFormUpdate
    template_name = 'baaswebapp/model_edit_form.html'

    def get_form(self, form_class=ThesisFormUpdate):
        form = super().get_form(form_class)
        form.helper = ThesisFormLayout(new=False)
        return form

    def form_valid(self, form):
        super().form_valid(form)
        EventLog.track(EventBaas.UPDATE_THESIS,
                       self.request.user.id,
                       form.instance.field_trial.id)
        return HttpResponseRedirect(self.get_success_url())


class ThesisDeleteView(LoginRequiredMixin, DeleteView):
    model = Thesis
    template_name = 'trialapp/thesis_delete.html'

    def get_success_url(self) -> str:
        return reverse(
            'thesis-list',
            kwargs={'field_trial_id': self.get_object().field_trial_id})

    def form_valid(self, form):
        EventLog.track(
                EventBaas.DELETE_THESIS,
                self.request.user.id,
                self._trial_id)
        return super().form_valid(form)


class ThesisApi(LoginRequiredMixin, DetailView):
    model = Thesis
    template_name = 'trialapp/thesis_show.html'
    context_object_name = 'thesis'

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        self._thesis = self.get_object()
        trial = self._thesis.field_trial
        headerRows = LayoutTrial.headerLayout(trial)
        layout = LayoutTrial.showLayout(
            self._thesis.field_trial, None,
            Thesis.getObjects(trial),
            onlyThis=self._thesis.id)
        treatments = [{'name': tt.getName(), 'id': tt.id}
                      for tt in TreatmentThesis.getObjects(self._thesis)]
        permisions = TrialPermission(trial, self.request.user).getPermisions()
        return {**context,
                'fieldTrial': trial,
                'title': self._thesis.getTitle(),
                'thesisVolume': self.getThesisVolume(),
                'treatments': treatments,
                'rowsReplicaHeader': headerRows,
                'rowsReplicas': layout,
                **permisions}

    def getThesisVolume(self):
        trial = self._thesis.field_trial
        appVolume = trial.application_volume
        if appVolume is None:
            return {
                'value': 'Missing Data: Volume',
                'detail': 'Please define Application Volume in field trial'}

        grossArea = trial.gross_surface
        if grossArea is None:
            return {'value': 'Missing Data: Gross area',
                    'detail': 'Please define Gross Surface in trial'}

        replicas_per_thesis = trial.replicas_per_thesis
        blocks = trial.blocks

        numberThesis = Thesis.getObjects(trial).count()

        litres = grossArea * appVolume * replicas_per_thesis
        surfacePerThesis = (numberThesis * blocks * 10000)
        thesisVolume = litres / surfacePerThesis
        rounding = 2
        unit = 'L'
        if thesisVolume < 1.0:
            thesisVolume = thesisVolume * 1000
            unit = 'mL'
            rounding = 0

        detail = 'Volumen per thesis for a {} L/Ha as application volumen, '\
                 ' on a gross area of {} m2 and {} thesis'.format(
                    appVolume, grossArea, numberThesis)
        return {'value': '{} {}'.format(round(thesisVolume, rounding), unit),
                'detail': detail}


class TreatmentThesisSetView(LoginRequiredMixin, View):
    model = TreatmentThesis
    template_name = 'trialapp/treatment_select.html'

    # see generateDataPointId
    # 3 thing can happen here:
    # - first time. There will be no product nor treatment,
    #   then show all products and all treatments
    # - product is selected, then filter product´ treatments
    # - treatment is selected, then assign that treatment to thesis
    #   and redirect to tesis
    def get(self, request, *args, **kwargs):
        theId = kwargs.get('thesis_id', None)
        thesis = get_object_or_404(Thesis, pk=theId)

        treatmentId = request.GET.get('treatment', None)
        if treatmentId:
            TreatmentThesis.findOrCreate(
                thesis=thesis,
                treatment_id=int(treatmentId))
            EventLog.track(
                EventBaas.UPDATE_THESIS,
                request.user.id,
                thesis.field_trial_id)
            return HttpResponseRedirect(thesis.get_absolute_url())

        productId = request.GET.get('product', None)
        products = Product.getSelectList(asDict=True)
        currentTreatment = ''
        if productId:
            productId = int(productId)
            treatments = Treatment.objects.filter(
                batch__product_variant__product_id=productId)
            currentTreatment = 0
        else:
            treatments = Treatment.objects.all()
            productId = ''

        treatments = treatments.order_by(
                'batch__product_variant__product__name',
                'batch__product_variant__name',
                'batch__name',
                'rate')
        treats = TreatmentThesis._getSelectList(treatments,
                                                asDict=True)
        return render(request, self.template_name,
                      {'thesis': thesis,
                       'title': f'Add treatment to [{thesis.name}]',
                       'fieldTrial': thesis.field_trial,
                       'productId': productId,
                       'products': products,
                       'currentTreatment': currentTreatment,
                       'treatments': treats})


class TreatmentThesisDeleteView(LoginRequiredMixin, DeleteView):
    model = TreatmentThesis
    template_name = 'trialapp/treatment_thesis_delete.html'

    def get_success_url(self) -> str:
        return reverse(
            'thesis_api',
            kwargs={'pk': self.get_object().thesis_id})

    def form_valid(self, form):
        EventLog.track(
                EventBaas.UPDATE_THESIS,
                self.request.user.id,
                self.get_object().thesis.field_trial_id)
        return super().form_valid(form)


class SetReplicaPosition(APIView):
    authentication_classes = []
    permission_classes = []
    http_method_names = ['post']

    # see generateDataPointId
    def post(self, request, x, y, oldReplicaId):
        newReplicaId = request.POST['replica_position']
        newReplica = None
        trialId = None
        if newReplicaId != '':
            newReplica = get_object_or_404(Replica, pk=newReplicaId)
            trialId = newReplica.thesis.field_trial_id

        oldReplica = None
        if oldReplicaId != 0:
            oldReplica = get_object_or_404(Replica, pk=oldReplicaId)
            trialId = oldReplica.thesis.field_trial_id

        # try to find if exists:
        if oldReplica:
            newPosX = 0
            newPosY = 0
            if newReplica:
                newPosX = newReplica.pos_x
                newPosY = newReplica.pos_y
            oldReplica.pos_x = newPosX
            oldReplica.pos_y = newPosY
            oldReplica.save()

        if newReplica:
            newReplica.pos_x = x
            newReplica.pos_y = y
            newReplica.save()
        EventLog.track(
                EventBaas.UPDATE_THESIS,
                0,  # TODO request.user.id if request.user.id else 0,
                trialId)
        return redirect('thesis-list', field_trial_id=trialId)
