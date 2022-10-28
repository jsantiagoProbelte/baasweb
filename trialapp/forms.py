
from django import forms
from crispy_forms.helper import FormHelper
from crispy_forms.layout import Layout, Div, Submit, Row, Field
from crispy_forms.bootstrap import FormActions
from .models import FieldTrial


class MyDateInput(forms.widgets.DateInput):
    def get_context(self, name, value, attrs):
        context = super().get_context(name, value, attrs)
        # use the browser's HTML date picker (no css/javascript required)
        context['widget']['type'] = 'date'
        return context


class FieldTrialCreateForm(forms.Form):

    field_trial_id = forms.CharField(widget=forms.HiddenInput())

    name = forms.CharField(label="Field Trial Name")
    phase = forms.ChoiceField(label="Phase",
                              required=True, choices=[])
    project = forms.ChoiceField(label="Project",
                                required=True, choices=[])
    objective = forms.ChoiceField(label="Objective",
                                  required=True, choices=[])
    responsible = forms.CharField(label="Responsible")
    farmer = forms.CharField(label="Farmer")

    product = forms.ChoiceField(label="Main Product", required=True, choices=[])
    crop = forms.ChoiceField(label="Crop", required=True, choices=[])
    plague = forms.ChoiceField(label="Plague", required=False, choices=[])

    initiation_date = forms.DateField(widget=MyDateInput(), required=True)
    location = forms.CharField(label="City/Area")
    rows_layout = forms.CharField(label="Layout. Number of rows",
                                  widget=forms.NumberInput())
    replicas_per_thesis = forms.CharField(
        label="Layout. Number of replicas per thesis",
        widget=forms.NumberInput())

    def __init__(self, *args, **kwargs):
        fieldValues = FieldTrial.extractValueModelChoicesFromKwargs(kwargs)
        super().__init__(*args, **kwargs)
        for label in fieldValues:
            self.fields[label].choices = fieldValues[label]
        self.helper = FormHelper()
        self.helper.form_id = 'id-create-field-trial'
        self.helper.form_class = 'create-field-trial'
        self.helper.form_method = 'post'
        self.helper.form_action = 'fieldtrial-save'

        text = 'Create Field Trial'
        if 'initial' in kwargs and \
           'field_trial_id' in kwargs['initial'] and \
           kwargs['initial']['field_trial_id'] is not None:
            text = 'Save'

        self.helper.layout = Layout(
            Row(
                Div(
                    Field('field_trial_id'),
                    Field('name'),
                    css_class='col-md-6'),
                Div(
                    Field('rows_layout'),
                    css_class='col-md-3'),
                Div(
                    Field('replicas_per_thesis'),
                    css_class='col-md-3'),
                css_class='mb-2'
            ),
            Row(
                Div(
                    Field('project', css_class='mb-2'),
                    Field('objective', css_class='mb-2'),
                    Field('phase', css_class='mb-2'),
                    Field('initiation_date',
                          css_class='mb-2'),
                    css_class='col-md-4'
                ),
                Div(
                    Field('product', css_class='mb-2'),
                    Field('crop', css_class='mb-2'),
                    Field('plague', css_class='mb-2'),
                    css_class='col-md-4'),
                Div(
                    Field('responsible', css_class='mb-2'),
                    Field('farmer', css_class='mb-2'),
                    Field('location', css_class='mb-2'),
                    css_class='col-md-4'),
            ),
            Row(
                Div(
                    FormActions(
                        Submit('submit', text,
                               css_class="btn btn-info")),
                    css_class='col-md-12 text-sm-end'),
            )
        )


class ThesisEditForm(forms.Form):
    field_trial_id = forms.CharField(widget=forms.HiddenInput())
    thesis_id = forms.CharField(widget=forms.HiddenInput())
    number = forms.CharField(
        label='Number', required=True,
        widget=forms.NumberInput())
    name = forms.CharField(label='Name', required=True)
    description = forms.CharField(label="Description", required=False,
                                  widget=forms.Textarea(attrs={'rows': 3}))
    product = forms.ChoiceField(label="Main Product", required=True,
                                choices=[])
    rate = forms.CharField(
        label='Rate', required=True,
        widget=forms.NumberInput())
    rate_unit = forms.ChoiceField(label="Main Product", required=True,
                                  choices=[])

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.helper = FormHelper()
        self.helper.form_id = 'id-edit-thesis'
        self.helper.form_class = 'create-thesis'
        self.helper.form_method = 'post'
        self.helper.form_action = '/save_thesis'

        text = 'Create Thesis'
        if 'initial' in kwargs and \
           'thesis_id' in kwargs['initial'] and \
           kwargs['initial']['thesis_id'] is not None:
            text = 'Save'

        self.helper.layout = Layout(
            Field('field_trial_id'),
            Field('thesis_id'),
            Row(
                Div(
                    Field('number'),
                    css_class='col-md-4'),
                Div(
                    Field('name'),
                    css_class='col-md-8'),
                css_class='mb-4'),
            Field('description', css_class='mb-4 mt-2'),
            Div(
                FormActions(
                    Submit('submit', text,
                           css_class="btn btn-info")),
                css_class='text-sm-end')
            )


class ApplicationEditForm(forms.Form):
    field_trial_id = forms.CharField(widget=forms.HiddenInput())
    application_id = forms.CharField(widget=forms.HiddenInput())
    name = forms.CharField(label='Name', required=True)
    application_date = forms.DateField(widget=MyDateInput(), required=True)
    crop_stage_majority = forms.CharField(
        label='Crop Stage Majority', required=True,
        widget=forms.NumberInput())
    crop_stage_scale = forms.CharField(label='Crop Stage Scale', required=True)

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.helper = FormHelper()
        self.helper.form_id = 'id-edit-application'
        self.helper.form_class = 'create-application'
        self.helper.form_method = 'post'
        self.helper.form_action = '/save_application'

        text = 'Create Application'
        if 'initial' in kwargs and \
           'application_id' in kwargs['initial'] and \
           kwargs['initial']['application_id'] is not None:
            text = 'Save'

        self.helper.layout = Layout(
            Field('field_trial_id'),
            Field('application_id'),
            Row(
                Div(
                    Field('application_date', css_class='mb-3'),
                    Field('crop_stage_majority', css_class='mb-4'),
                    css_class='col-md-6'),
                Div(
                    Field('name', css_class='mb-3'),
                    Field('crop_stage_scale', css_class='mb-4'),
                    css_class='col-md-6'),
                css_class=''),
            Div(
                FormActions(
                    Submit('submit', text,
                           css_class="btn btn-info")),
                css_class='text-sm-end')
            )
