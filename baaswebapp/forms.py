"""
Definition of forms.
"""

from django import forms
from django.contrib.auth.forms import AuthenticationForm
from django.utils.translation import gettext_lazy as _
from crispy_forms.helper import FormHelper
from crispy_forms.layout import Layout, Div, Submit, Field
from crispy_forms.bootstrap import FormActions


class BootstrapAuthenticationForm(AuthenticationForm):
    """Authentication form which uses boostrap CSS."""
    username = forms.CharField(
        max_length=254,
        widget=forms.TextInput({
            'class': 'form-control',
            'placeholder': 'User name'}))
    password = forms.CharField(
        label=_("Password"),
        widget=forms.PasswordInput({
            'class': 'form-control',
            'placeholder': 'Password'}))

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.helper = FormHelper()
        self.helper.form_id = 'id-login'
        self.helper.form_class = 'login-form'
        self.helper.form_method = 'post'
        self.helper.form_action = 'login'
        self.helper.layout = Layout(
            Div(
                Field('username', css_class='mb-3'),
                Field('password', css_class='mb-3'),
                FormActions(
                    Submit(
                        'submit',
                        'Login',
                        css_class="btn btn-primary float-end"))
                )
            )
