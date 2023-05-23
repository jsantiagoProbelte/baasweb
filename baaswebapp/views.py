from django.http import HttpResponse, HttpRequest
from datetime import datetime
from django.shortcuts import render, redirect
from django.conf import settings
from django.contrib.auth import logout, authenticate, login
from django.contrib import messages
from django.contrib.auth.forms import AuthenticationForm
from baaswebapp.forms import BootstrapAuthenticationForm
from baaswebapp.data_loaders import TrialStats


def home(request):
    """Renders the home page."""
    assert isinstance(request, HttpRequest)
    stats = TrialStats.getGeneralStats()
    return render(
        request,
        'baaswebapp/index.html',
        {
            'title': 'Home Page',
            'year': datetime.now().year,
            'Products': stats['products'],
            'FieldTrials': stats['field_trials'],
            'LabTrials': stats['lab_trials'],
            'DataPoints': stats['points']
        }
    )


def baaswebapp_index(request):
    testValue = settings.DEBUG
    expectedText = "This is BaaS in mode DEBUG= {}."
    return HttpResponse(expectedText.format(testValue))


def logout_request(request):
    logout(request)
    messages.info(request, "Logged out successfully!")
    return redirect("home")


def login_request(request):
    if request.method == 'POST':
        form = AuthenticationForm(request=request, data=request.POST)
        if form.is_valid():
            username = form.cleaned_data.get('username')
            password = form.cleaned_data.get('password')
            user = authenticate(username=username, password=password)
            if user is not None:
                login(request, user)
                return redirect('/')
            else:
                messages.error(request, "Invalid username or password.")
        else:
            messages.error(request, "Invalid username or password.")

    formLogin = BootstrapAuthenticationForm()
    return render(
        request=request,
        template_name="baaswebapp/login.html",
        context={"formLogin": formLogin})
