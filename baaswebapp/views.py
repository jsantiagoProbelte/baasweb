from django.http import HttpResponse, HttpRequest
from datetime import datetime
from django.shortcuts import render, redirect
from django.conf import settings
from django.contrib.auth import logout, authenticate, login
from django.contrib import messages
from django.contrib.auth.models import User
from django.contrib.auth.forms import AuthenticationForm
from baaswebapp.forms import BootstrapAuthenticationForm, CreateInviteForm
from baaswebapp.data_loaders import TrialStats
from baaswebapp.models import FaceIdUser


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


def invite_request(request):
    invite_url = None

    if not request.user.is_superuser:
        res = home(request)
        return res

    if request.method == 'POST':
        form = CreateInviteForm(request.POST)
        if form.is_valid():
            username = form.cleaned_data.get('username')
            first_name = form.cleaned_data.get('first_name')
            last_name = form.cleaned_data.get('last_name')
            email = form.cleaned_data.get('email')
            user = User.objects.create(
                username=username, first_name=first_name, last_name=last_name,
                email=email)
            faceid_user = FaceIdUser.objects.create(
                user=user)
            invite_code = faceid_user.invite_code
            invite_url = request.META['HTTP_HOST'] + \
                "/accept?invite_code=" + str(invite_code)
        else:
            messages.error(request, "Invalid data.")

    formInvite = CreateInviteForm()
    return render(
        request=request,
        template_name="baaswebapp/invite.html",
        context={"formInvite": formInvite, "inviteUrl": invite_url}
    )


def accept_request(request):
    if request.method == 'POST':
        pass

    invite_code = request.GET.get('invite_code')
    if not invite_code:
        messages.error(request, "Invite link invalid.")
    faceid_user = FaceIdUser.objects.get(invite_code=invite_code)

    return render(
        request=request,
        template_name="baaswebapp/accept.html",
        context={"user": faceid_user.user}
    )
