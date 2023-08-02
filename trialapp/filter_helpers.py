from django.db.models import Q, Count
import django_filters
from trialapp.models import FieldTrial, Crop, Plague


class TrialFilter(django_filters.FilterSet):
    crop = django_filters.ModelChoiceFilter(
        queryset=Crop.objects.all().order_by('name'))
    plague = django_filters.ModelChoiceFilter(
        queryset=Plague.objects.all().order_by('name'))

    class Meta:
        model = FieldTrial
        fields = ['crop', 'plague']


class TrialFilterHelper:
    _attributes = None
    _trials = None

    # Add self.request.GET as attributes
    def __init__(self, attributes):
        self._attributes = attributes.copy()

    # add extra param:
    def addProduct(self, product):
        self._attributes['product'] = product

    # add extra param:
    def addCrop(self, crop):
        self._attributes['crop'] = crop

    # add extra param:
    def addPlague(self, plague):
        self._attributes['plague'] = plague

    # add extra text:
    def addText(self, text):
        self._attributes['name'] = text

    def filter(self):
        q_objects = self.prepareFilter()
        self.getTrialList(q_objects)

    def getAttrValue(self, label):
        value = self._attributes.get(label, None)
        return None if value == '' else value

    def getTrialList(self, filter):
        self._trials = FieldTrial.objects.filter(filter)

    def prepareFilter(self):
        paramsReplyTemplate = TrialFilter.Meta.fields
        q_objects = Q(trial_meta=FieldTrial.TrialMeta.FIELD_TRIAL)
        for paramIdName in paramsReplyTemplate:
            paramId = self.getAttrValue(paramIdName)
            if paramIdName == 'name' and paramId:
                q_name = Q()
                q_name |= Q(name__icontains=paramId)
                q_name |= Q(responsible__icontains=paramId)
                q_name |= Q(code__icontains=paramId)
                q_objects &= q_name
            elif paramId:
                q_objects &= Q(**({'{}__id'.format(paramIdName): paramId}))
        return q_objects

    def countTrials(self):
        return self._trials.count()

    def countProductCategories(self):
        return self.countBy('product__category__name')

    def countBy(self, param):
        counts = self._trials.values(
            param
        ).annotate(
            total=Count('id')
        ).order_by(param)

        return {item[param]: item['total'] for item in counts}

    @classmethod
    def getCountFieldTrials(cls, product):
        return FieldTrial.objects.filter(product=product).count()
