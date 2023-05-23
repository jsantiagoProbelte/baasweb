# Create your views here.
from django.contrib.auth.mixins import LoginRequiredMixin
# from rest_framework import permissions
from trialapp.models import Application, FieldTrial
from django.shortcuts import get_object_or_404, render
from rest_framework.views import APIView
from django.views.generic.list import ListView
from django.views.generic.edit import CreateView, UpdateView, DeleteView
from crispy_forms.helper import FormHelper
from django.urls import reverse
from crispy_forms.layout import Layout, Div, Submit, Field, HTML
from crispy_forms.bootstrap import FormActions
from django.http import HttpResponseRedirect
from django import forms
from trialapp.forms import MyDateInput


class ApplicationListView(LoginRequiredMixin, ListView):
    model = Application
    paginate_by = 100  # if pagination is desired
    login_url = '/login'

    def get_context_data(self, **kwargs):
        field_trial_id = self.kwargs['field_trial_id']
        fieldTrial = get_object_or_404(FieldTrial, pk=field_trial_id)
        return {'object_list': Application.getObjects(fieldTrial),
                'fieldTrial': fieldTrial}


class ApplicationFormLayout(FormHelper):
    def __init__(self, new=True):
        super().__init__()
        title = 'New application' if new else 'Edit application'
        submitTxt = 'Create' if new else 'Save'
        self.add_layout(Layout(Div(
            HTML(title), css_class="h4 mt-4"),
            Div(Field('app_date', css_class='mb-3'),
                Field('bbch', css_class='mb-3'),
                Field('comment', css_class='mb-3'),
                FormActions(
                    Submit('submit', submitTxt, css_class="btn btn-info"),
                    css_class='text-sm-end'),
                css_class="card-body-baas mt-2")
            ))


class ApplicationForm(forms.ModelForm):
    class Meta:
        model = Application
        fields = ('app_date', 'bbch', 'comment')

    def __init__(self, *args, **kwargs):
        super(ApplicationForm, self).__init__(*args, **kwargs)
        self.fields['app_date'].label = "Application date"
        self.fields['app_date'].widget = MyDateInput()
        self.fields['comment'].required = False
        self.fields['bbch'].label = "Crop Stage Majority BBCH"
        self.fields['comment'].widget = forms.Textarea(attrs={'rows': 5})


class ApplicationCreateView(LoginRequiredMixin, CreateView):
    model = Application
    form_class = ApplicationForm
    template_name = 'baaswebapp/model_edit_form.html'

    def get_form(self, form_class=ApplicationForm):
        form = super().get_form(form_class)
        form.helper = ApplicationFormLayout()
        return form

    def form_valid(self, form):
        if form.is_valid():
            form.instance.field_trial_id = self.kwargs["field_trial_id"]
            application = form.instance
            application.save()
            Application.computeDDT(application.field_trial)
            return HttpResponseRedirect(application.get_success_url())


class ApplicationUpdateView(LoginRequiredMixin, UpdateView):
    model = Application
    form_class = ApplicationForm
    template_name = 'baaswebapp/model_edit_form.html'

    def get_form(self, form_class=ApplicationForm):
        form = super().get_form(form_class)
        form.helper = ApplicationFormLayout(new=False)
        return form

    def form_valid(self, form):
        if form.is_valid():
            application = form.instance
            application.save()
            Application.computeDDT(application.field_trial)
            return HttpResponseRedirect(application.get_success_url())


class ApplicationDeleteView(DeleteView):
    model = Application
    template_name = 'trialapp/application_delete.html'
    _trial = None

    def get_success_url(self):
        if self._trial is None:
            return '/fieldtrials/'
        else:
            return reverse(
                'assessment-list',
                kwargs={'field_trial_id': self._trial.id})

    def form_valid(self, form):
        self._trial = self.object.field_trial
        respose = super().form_valid(form)
        Application.computeDDT(self._trial)
        return respose


class ApplicationApi(APIView):
    authentication_classes = []
    permission_classes = []
    http_method_names = ['get']

    def get(self, request, *args, **kwargs):
        template_name = 'trialapp/application_show.html'
        application_id = kwargs['application_id']
        application = get_object_or_404(Application, pk=application_id)
        return render(
            request, template_name, {
                'fieldTrial': application.field_trial,
                'application': application})
