from django.http import HttpResponse
from baaswebapp.settings import DEBUG


def baaswebapp_index(request):
    testValue = DEBUG
    expectedText = "This is BaaS in mode DEBUG= {}."
    return HttpResponse(expectedText.format(testValue))
