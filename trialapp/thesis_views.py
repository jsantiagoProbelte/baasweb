# Create your views here.
from django.views.generic.list import ListView
from django.contrib.auth.mixins import LoginRequiredMixin
# from rest_framework import permissions
from trialapp.models import FieldTrial,\
    Thesis, Replica, TreatmentThesis
from django.shortcuts import get_object_or_404, render, redirect
from rest_framework.views import APIView
from trialapp.trial_helper import LayoutTrial
from django.views.generic.edit import CreateView, UpdateView, DeleteView
from crispy_forms.helper import FormHelper
from django.urls import reverse
from crispy_forms.layout import Layout, Div, Submit, Field, HTML
from crispy_forms.bootstrap import FormActions
from django.http import HttpResponseRedirect
from django import forms
from trialapp.trial_helper import MyDateInput
from catalogue.models import Treatment


class ThesisListView(LoginRequiredMixin, ListView):
    model = Thesis
    paginate_by = 100  # if pagination is desired
    login_url = '/login'

    def get_context_data(self, **kwargs):
        field_trial_id = self.kwargs['field_trial_id']
        fieldTrial = get_object_or_404(FieldTrial, pk=field_trial_id)
        allThesis, thesisDisplay = Thesis.getObjectsDisplay(fieldTrial)
        headerRows = LayoutTrial.headerLayout(fieldTrial)
        replicas = [
            {'value': item.id, 'number': item.thesis.number,
             'name': item.getTitle()}
            for item in Replica.getFieldTrialObjects(fieldTrial)]
        return {'thesisList': thesisDisplay,
                'fieldTrial': fieldTrial,
                'rowsReplicaHeader': headerRows,
                'replicas': replicas,
                'rowsReplicas': LayoutTrial.showLayout(fieldTrial,
                                                       None,
                                                       allThesis)}


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
        self.fields['first_application'].widget = MyDateInput()
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
        self.fields['first_application'].widget = MyDateInput()
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


class ThesisDeleteView(DeleteView):
    model = Thesis
    template_name = 'trialapp/thesis_delete.html'
    _trial_id = None

    def get_success_url(self):
        if self._trial_id is None:
            return '/fieldtrials/'
        else:
            return reverse(
                'thesis-list',
                kwargs={'field_trial_id': self._trial_id})

    def form_valid(self, form):
        self._trial_id = self.object.field_trial.id
        return super().form_valid(form)


class ThesisApi(APIView):
    authentication_classes = []
    permission_classes = []
    http_method_names = ['get']

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

    def get(self, request, *args, **kwargs):
        template_name = 'trialapp/thesis_show.html'
        thesis_id = kwargs['thesis_id']
        self._thesis = get_object_or_404(Thesis, pk=thesis_id)
        trial = self._thesis.field_trial
        headerRows = LayoutTrial.headerLayout(trial)
        layout = LayoutTrial.showLayout(
            self._thesis.field_trial, None,
            Thesis.getObjects(trial), onlyThis=thesis_id)
        treatments = [{'name': tt.getName(), 'id': tt.id}
                      for tt in TreatmentThesis.getObjects(self._thesis)]

        return render(
            request, template_name, {
                'fieldTrial': trial,
                'thesis': self._thesis,
                'title': self._thesis.getTitle(),
                'thesisVolume': self.getThesisVolume(),
                'treatments': treatments,
                'rowsReplicaHeader': headerRows,
                'rowsReplicas': layout})


class TreatmentThesisFormLayout(FormHelper):
    def __init__(self, thesisName):
        super().__init__()
        title = 'Add treatment to thesis [{}]'.format(thesisName)
        self.add_layout(Layout(Div(
            HTML(title), css_class="h4 mt-4"),
            Div(Field('treatment', css_class='mb-3'),
                FormActions(
                    Submit('submit', 'Add', css_class="btn btn-info"),
                    css_class='text-sm-end'),
                css_class="card-body-baas mt-2")
            ))


class TreatmentThesisForm(forms.ModelForm):
    class Meta:
        model = TreatmentThesis
        fields = ('treatment',)

    def __init__(self, *args, **kwargs):
        super(TreatmentThesisForm, self).__init__(*args, **kwargs)
        listt = Treatment.objects.all().order_by(
            'batch__product_variant__product__name',
            'batch__product_variant__name',
            'batch__name',
            'rate')
        self.fields['treatment'].queryset = listt


class TreatmentThesisCreateView(LoginRequiredMixin, CreateView):
    model = TreatmentThesis
    form_class = TreatmentThesisForm
    template_name = 'baaswebapp/model_edit_form.html'

    def get_form(self, form_class=TreatmentThesisForm):
        form = super().get_form(form_class)
        thesisName = Thesis.objects.get(id=self.kwargs['thesis_id'])
        form.helper = TreatmentThesisFormLayout(thesisName)
        return form

    def form_valid(self, form):
        if form.is_valid():
            thesis_id = self.kwargs["thesis_id"]
            treatmentThesis = form.instance
            treatmentThesis.thesis_id = thesis_id
            treatmentThesis.save()
            return HttpResponseRedirect(self.get_success_url(thesis_id))

    def get_success_url(self, thesis_id):
        return reverse(
            'thesis_api',
            kwargs={'thesis_id': thesis_id})


class TreatmentThesisDeleteView(DeleteView):
    model = TreatmentThesis
    template_name = 'trialapp/treatment_thesis_delete.html'
    _thesis = None

    def get_success_url(self):
        if self._thesis is None:
            return '/fieldtrials/'
        else:
            return self._thesis.get_absolute_url()

    def form_valid(self, form):
        self._thesis = self.object.thesis
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
        return redirect('thesis-list',
                        field_trial_id=trialId)
