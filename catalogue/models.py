from django.db import models
from baaswebapp.models import ModelHelpers


class Vendor(ModelHelpers, models.Model):
    name = models.CharField(max_length=100)
