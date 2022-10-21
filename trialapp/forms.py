
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

    product = forms.ChoiceField(label="Product", required=True, choices=[])
    crop = forms.ChoiceField(label="Crop", required=True, choices=[])
    plague = forms.ChoiceField(label="Plague", required=False, choices=[])

    initiation_date = forms.DateField(widget=MyDateInput(), required=True)
    completion_date = forms.DateField(widget=MyDateInput(), required=False)

    location = forms.CharField(label="City/Area")

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
            Div(
                Field('field_trial_id'),
                Field('name', css_class='mb-6')),
            Row(
                Div(
                    Field('product', css_class='mb-2'),
                    Field('crop', css_class='mb-2'),
                    Field('plague', css_class='mb-2'),
                    Field('project', css_class='mb-2'),
                    Field('objective', css_class='mb-2'),
                    Field('phase', css_class='mb-2'),
                    css_class='col-md-6'),
                Div(
                    Field('responsible', css_class='mb-2'),
                    Field('farmer', css_class='mb-2'),
                    Field('location', css_class='mb-2'),

                    Field('initiation_date', css_class='mb-2'),
                    Field('completion_date', css_class='mb-2'),
                    css_class='col-md-6'),
            ),
            Row(
                Div(
                    FormActions(
                        Submit('submit', text,
                               css_class="btn btn-primary "),
                        css_class='float-end'),
                    css_class='col-md-12 text-right'),
            )
        )
