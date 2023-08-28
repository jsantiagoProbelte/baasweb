from django.http import HttpResponse, HttpRequest
from datetime import datetime
from django.shortcuts import render, redirect
from django.conf import settings
from django.contrib.auth import logout, authenticate, login
from django.contrib import messages
from django.contrib.auth.forms import AuthenticationForm
from django.contrib.auth.models import User
from baaswebapp.forms import BootstrapAuthenticationForm
from baaswebapp.data_loaders import TrialStats
from sesame.utils import get_query_string
import sendgrid
from sendgrid.helpers.mail import Email, To, Content, Mail

sg = sendgrid.SendGridAPIClient(
    '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')


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


def login_request_passkey(request):
    if request.method == 'POST':
        user = authenticate(
            request, username=request.POST["username"], password=request.POST["password"])
        if user is not None:
            login(request, user)
            return redirect('/')
        else:
            messages.error(request, "Invalid passkey")

    formLogin = BootstrapAuthenticationForm()
    return render(
        request=request,
        template_name="baaswebapp/login.html",
        context={"formLogin": formLogin})


def login_email(request):
    if request.method != 'POST':
        return redirect('/login')
    user = User.objects.get(username=request.POST["username"])
    print(user)
    LOGIN_URL = "https://localhost:8000/sesame/login/"
    LOGIN_URL += get_query_string(user)
    print(LOGIN_URL)
    from_email = Email("alex@arentz.cc")
    to_email = To("aleksanderarentz@gmail.com")
    subject = "Your Login Request to BaasWeb"
    content = Content(
        "text/plain", "Press the following link to sign in: " + LOGIN_URL)
    mail = Mail(from_email, to_email, subject, content)
    mail_response = sg.client.mail.send.post(request_body=mail.get())
    print(mail_response.status_code)
    print(mail_response.body)
    print(mail_response.headers)

    return redirect('/')


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
