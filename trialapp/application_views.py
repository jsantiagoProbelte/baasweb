# Create your views here.
from django.contrib.auth.mixins import LoginRequiredMixin
# from rest_framework import permissions
from trialapp.models import Application, FieldTrial
from django.shortcuts import get_object_or_404
from django.views.generic.list import ListView
from django.views.generic import DetailView
from django.views.generic.edit import CreateView, UpdateView, DeleteView
from crispy_forms.helper import FormHelper
from django.urls import reverse
from crispy_forms.layout import Layout, Div, Submit, Field, HTML
from crispy_forms.bootstrap import FormActions
from django.http import HttpResponseRedirect
from django import forms
from trialapp.trial_helper import TrialPermission


class ApplicationListView(LoginRequiredMixin, ListView):
    model = Application
    paginate_by = 100  # if pagination is desired
    login_url = '/login'

    def get_context_data(self, **kwargs):
        field_trial_id = self.kwargs['field_trial_id']
        fieldTrial = get_object_or_404(FieldTrial, pk=field_trial_id)
        permisions = TrialPermission(
            fieldTrial, self.request.user).getPermisions()
        return {'object_list': Application.getObjects(fieldTrial),
                'fieldTrial': fieldTrial,
                **permisions}


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
        self.fields['app_date'].widget = forms.DateInput(
            format=('%Y-%m-%d'),
            attrs={'class': 'form-control',
                   'type': 'date'})
        self.fields['app_date'].show_hidden_initial = True
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


class ApplicationDeleteView(LoginRequiredMixin, DeleteView):
    model = Application
    template_name = 'trialapp/application_delete.html'
    _parent = None

    def delete(self, request, *args, **kwargs):
        self.object = self.get_object()
        self._parent = self.object.field_trial
        self.object.delete()
        Application.computeDDT(self._parent)
        return HttpResponseRedirect(self.get_success_url())

    def get_success_url(self):
        if self._parent:
            return reverse('application-list',
                           kwargs={'field_trial_id': self._parent.id})
        else:
            return reverse('trial-list')


class ApplicationApi(LoginRequiredMixin, DetailView):
    model = Application
    template_name = 'trialapp/application_show.html'
    context_object_name = 'application'

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        trial = self.get_object().field_trial
        permisions = TrialPermission(trial, self.request.user).getPermisions()
        return {**context,
                'fieldTrial': trial,
                **permisions}
