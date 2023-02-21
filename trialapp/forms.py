
from django import forms
from crispy_forms.helper import FormHelper
from crispy_forms.layout import Layout, Div, Submit, Row, Field, HTML
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
    code = forms.CharField(label=False)
    name = forms.CharField(label=False, widget=forms.TextInput(
        attrs={'placeholder': 'Field Trial name'}))
    trial_type = forms.ChoiceField(label="Type",
                                   required=True, choices=[])
    trial_status = forms.ChoiceField(label="Status",
                                     required=True, choices=[])
    project = forms.ChoiceField(label="Project",
                                required=True, choices=[])
    objective = forms.ChoiceField(label="Objective",
                                  required=True, choices=[])
    responsible = forms.CharField(label="Responsible")
    contact = forms.CharField(label="Farmer")
    cro = forms.CharField(label="CRO", required=False)
    description = forms.CharField(
        label="Description",
        required=False,
        widget=forms.Textarea(attrs={'rows': 10}))

    ref_to_eppo = forms.CharField(label="EPPO Reference", required=False)
    ref_to_criteria = forms.CharField(label="Criteria Reference",
                                      required=False)
    comments_criteria = forms.CharField(
        label="Criteria comments",
        required=False,
        widget=forms.Textarea(attrs={'rows': 5}))

    product = forms.ChoiceField(label="Main Product",
                                required=True, choices=[])
    crop = forms.ChoiceField(label="Crop", required=True, choices=[])
    plague = forms.ChoiceField(label="Plague", required=False, choices=[])

    initiation_date = forms.DateField(widget=MyDateInput(), required=True)
    completion_date = forms.DateField(widget=MyDateInput(), required=False)
    location = forms.CharField(label="City/Area")
    blocks = forms.CharField(label="# blocks",
                             widget=forms.NumberInput())
    replicas_per_thesis = forms.CharField(
        label="# replicas",
        widget=forms.NumberInput())
    samples_per_replica = forms.CharField(
        label="# samples", required=False,
        widget=forms.NumberInput())
    distance_between_plants = forms.CharField(
        label="Plants separation", required=False)
    distance_between_rows = forms.CharField(
        label="Rows separation", required=False)
    number_rows = forms.CharField(
        label="# rows", required=False)
    lenght_row = forms.CharField(
        label="Row length (m)", required=False)
    net_surface = forms.CharField(
        label="Net area plot (m2)", required=False)
    gross_surface = forms.CharField(
        label="Gross area plot (m2)", required=False)

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
        title = 'New'
        if 'initial' in kwargs and \
           'field_trial_id' in kwargs['initial'] and \
           kwargs['initial']['field_trial_id'] is not None:
            text = 'Save'
            title = 'Edit'

        self.helper.layout = Layout(
            Row(Div(HTML(title),
                    css_class='col-md-1 h2'),
                Div(Field('code'),
                    css_class='col-md-2'),
                Div(Field('field_trial_id'),
                    Field('name'),
                    css_class='col-md-7'),
                Div(FormActions(
                        Submit('submit', text, css_class="btn btn-info")),
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
                    css_class='col-md-4')))


class EvaluationEditForm(forms.Form):
    field_trial_id = forms.CharField(widget=forms.HiddenInput())
    evaluation_id = forms.CharField(widget=forms.HiddenInput())
    name = forms.CharField(label='Name', required=True)
    evaluation_date = forms.DateField(widget=MyDateInput(), required=True)
    crop_stage_majority = forms.CharField(
        label='Crop Stage Majority (BBCH)', required=True,
        widget=forms.NumberInput())

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.helper = FormHelper()
        self.helper.form_id = 'id-edit-evaluation'
        self.helper.form_class = 'create-evaluation'
        self.helper.form_method = 'post'
        self.helper.form_action = '/save_evaluation'

        text = 'Create Evaluation'
        if 'initial' in kwargs and \
           'evaluation_id' in kwargs['initial'] and \
           kwargs['initial']['evaluation_id'] is not None:
            text = 'Save'

        self.helper.layout = Layout(
            Field('field_trial_id'),
            Field('evaluation_id'),
            Field('evaluation_date', css_class='mb-3'),
            Field('crop_stage_majority', css_class='mb-4'),
            Field('name', css_class='mb-3'),
            FormActions(
                Submit('submit', text, css_class="btn btn-info"),
                css_class='text-sm-end'))
