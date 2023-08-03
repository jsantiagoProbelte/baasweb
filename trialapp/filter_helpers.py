from django.db.models import Q, Count, Min, Max
import django_filters
from trialapp.models import FieldTrial, Crop, Plague
from catalogue.models import Product
from django.contrib.auth.mixins import LoginRequiredMixin
from django.views.generic import View
from django.http import HttpResponseRedirect
from django_filters.views import FilterView
from baaswebapp.models import ModelHelpers
from baaswebapp.graphs import ProductCategoryGraph


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
    _trialFilter = None

    KEY_PER_CLS = {Product: 'product_id',
                   Crop: 'crop_id',
                   Plague: 'plague_id'}

    # Add self.request.GET as attributes
    def __init__(self, attributes):
        self.setTrialFilter(attributes)

    def setTrialFilter(self, attributes):
        # Take of remove empty values
        self._attributes = {}
        for key in attributes:
            value = attributes.get(key, None)
            if value:
                self._attributes[key] = value
        self._trialFilter = TrialFilter(self._attributes)

    def getFilter(self):
        return self._trialFilter

    def filter(self):
        q_objects = self.prepareFilter()
        self.filterTrials(q_objects)

    def getTrials(self):
        return self._trials

    def getClsObjects(self, cls):
        if len(self._attributes) > 0:
            trialIds = [item.id for item in self._trials]
            keyPerCls = TrialFilterHelper.KEY_PER_CLS.get(cls, None)
            if keyPerCls:
                valuesIds = FieldTrial.objects.filter(
                    id__in=trialIds).values(keyPerCls)
                ids = [item[keyPerCls] for item in valuesIds]
                return cls.objects.filter(id__in=ids)
        return cls.objects.all()

    def getAttrValue(self, label):
        value = self._attributes.get(label, None)
        return None if value == '' else value

    def filterTrials(self, filter):
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
                q_name |= Q(product__active_substance=paramId)
                q_objects &= q_name
            elif paramId:
                q_objects &= Q(**({'{}__id'.format(paramIdName): paramId}))
        return q_objects

    def countTrials(self):
        return len(self._trials)

    def countProductCategories(self):
        return self.countBy('product__category__name')

    def countBy(self, param):
        counts = self._trials.values(
            param
        ).annotate(
            total=Count('id')
        ).order_by(param)

        return {item[param]: item['total'] for item in counts}

    def generateParamUrl(self):
        params = ''
        for attribute in self._attributes:
            params += f'&{attribute}={self._attributes[attribute]}'
        return params

    @classmethod
    def getCountFieldTrials(cls, product):
        return FieldTrial.objects.filter(product=product).count()

    @staticmethod
    def colorCategory(name):
        # Returns a css class from baaswebapp.css
        if name in ['Biofertilizer', 'Fertilizer']:
            return 'bs_nutritional'
        elif name in ['Bioestimulant']:
            return 'bs_estimulant'
        elif name in ['Biocontrol', 'Biofungicide', 'Bionematicide',
                      'Bioherbicide', 'Fungicide', 'Nematicide',
                      'Herbicide']:
            return 'bs_control'
        else:
            return 'bs_category_unknown'

    def getMinMaxYears(self, product):
        # Step 1: Retrieve the list of items with the date attribute
        items = self._trials.filter(product=product)
        # Step 2: Use Django's aggregation functions to find the min
        # and maximum dates
        min_date = items.aggregate(Min('initiation_date'))[
            'initiation_date__min']
        max_date = items.aggregate(Max('initiation_date'))[
            'initiation_date__max']
        # Step 3: Extract the years from the dates
        min_year = min_date.year if min_date else None
        max_year = max_date.year if max_date else None

        # Step 4: Return the minimum and maximum years
        if min_year is None:
            return '-'
        elif min_year == max_year:
            return f'{min_year}'

        return f'{min_year}-{max_year}'


class BaaSView(LoginRequiredMixin, View):
    model = FieldTrial
    template_name = 'trialapp/treatment_select.html'

    PRODUCT = 'product'
    CROP = 'crop'
    PLAGUE = 'plague'
    TRIALS = 'trials'
    # value on select : (label on select , url )
    GROUP_BY = {PRODUCT: ('Product', 'products'),
                CROP: ('Crop', 'products'),
                PLAGUE: ('Plague', 'products'),
                TRIALS: ('Ungrouped', 'trials')}

    @staticmethod
    def groupByOptions():
        return [{'value': item,
                 'name': BaaSView.GROUP_BY[item][0]}
                for item in BaaSView.GROUP_BY]

    def get(self, request, *args, **kwargs):
        groupbyTag = request.GET.get('groupby', None)
        redirectTuple = BaaSView.GROUP_BY.get(groupbyTag, (0, 'product'))
        return HttpResponseRedirect(redirectTuple[1])


class TrialListView(LoginRequiredMixin, FilterView):
    model = FieldTrial
    paginate_by = 100  # if pagination is desired
    login_url = '/login'
    template_name = 'baaswebapp/baas_view_list.html'

    def get_context_data(self, **kwargs):
        new_list = []
        fHelper = TrialFilterHelper(self.request.GET)
        fHelper.filter()
        objectList = fHelper.getTrials().order_by('-code')
        num_trials = fHelper.countTrials()
        countCategories = fHelper.countProductCategories()
        graphCategories = ProductCategoryGraph.draw(countCategories)
        products = set()
        for item in objectList:
            category = ModelHelpers.UNKNOWN
            products.add(item.product.id)
            if item.product.category:
                category = item.product.category.name
            description = f'{item.crop}'
            if item.plague:
                description += f' + {item.plague}'

            new_list.append({
                'code': item.code,
                'description': description,
                'location': item.location if item.location else '',
                'active_substance': item.product.active_substance,
                'product': item.product,
                'category': category,
                'color_category': TrialFilterHelper.colorCategory(category),
                'efficacies': '??',
                'date_range': item.initiation_date.year if item.initiation_date
                              else '',
                'trials': '',
                'id': item.id})
        return {'object_list': new_list,
                'num_products': len(products),
                'trialfilter': fHelper.getFilter(),
                'groupbyfilter': BaaSView.groupByOptions(),
                'groupby': BaaSView.TRIALS,
                'num_trials': num_trials,
                'graphCategories': graphCategories,
                'extra_params': fHelper.generateParamUrl()}
