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
from django.utils.translation import activate

sg = sendgrid.SendGridAPIClient(settings.SENDGRID_KEY)


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
    current_url = request.build_absolute_uri().rsplit('/', 1)[0]
    LOGIN_URL = current_url + "/sesame/login/" + get_query_string(user)
    html_content = "<html><p>Welcome to BaaS! Click <a href=" + \
        LOGIN_URL + ">here</a> to sign in!</p</html>"
    from_email = Email("jsantiago@probelte.com")
    to_email = To(user.email)
    subject = "Your Login Request to BaaS"
    content = Content(
        "text/html", html_content)
    mail = Mail(from_email, to_email, subject, content)
    sg.client.mail.send.post(request_body=mail.get())
    messages.info(
        request, "Email has been sent! Check your inbox for a URL to sign in!")
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


def change_language(request, language_code):
    activate(language_code)
    request.session['django_language'] = language_code
    return redirect(request.META.get('HTTP_REFERER', '/'))
