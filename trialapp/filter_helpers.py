from django.db.models import Q, Count, Min, Max
import django_filters
from trialapp.models import FieldTrial, Crop, Plague
from catalogue.models import Product
from django.contrib.auth.mixins import LoginRequiredMixin
from django.views.generic import View
from django.http import HttpResponseRedirect
from django_filters.views import FilterView
from baaswebapp.models import ModelHelpers
from baaswebapp.graphs import ProductCategoryGraph, COLOR_control, \
    COLOR_estimulant, COLOR_nutritional, COLOR_unknown


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

    COLOR_CATEGORY = {
        Product.Category.NUTRITIONAL: 'bg-nutritional',
        Product.Category.ESTIMULANT: 'bg-estimulant',
        Product.Category.CONTROL: 'bg-control',
        Product.Category.UNKNOWN: 'bg-unknown'}
    COLOR_CODE = {
        'bg-nutritional': COLOR_nutritional,
        'bg-estimulant': COLOR_estimulant,
        'bg-control': COLOR_control,
        'bg-unknown': COLOR_unknown}

    # LABEL_CATEGORY = {
    #     NUTRITIONAL: 'nutritional',
    #     ESTIMULANT: 'estimulant',
    #     CONTROL: 'control',
    #     UNKNOWN: 'unknown'}

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
        paramsReplyTemplate = TrialFilter.Meta.fields + ['name']
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
        counts = self.countBy('product__type_product')
        countCategories = {}
        for productType in counts:
            category = Product.getCategory(productType)
            label = category.label
            if label not in countCategories:
                color = TrialFilterHelper.colorCategory(category)
                codeColor = TrialFilterHelper.COLOR_CODE[color]
                countCategories[label] = {'value': 0,
                                          'color': codeColor}
            countCategories[label]['value'] += counts[productType]
        return countCategories

    def countProducts(self):
        return len(list(self.countBy('product', True).keys()))

    def countBy(self, param, isDistinct=False):
        counts = self._trials.values(
            param
        ).annotate(
            total=Count('id', distinct=isDistinct)
        ).order_by(param)
        return {item[param]: item['total'] for item in counts}

    def countProductCategoriesAndCrop(self):
        cropProducts = {}
        productIds = set()
        # Scan products in trials
        for trial in self._trials:
            cropId = trial.crop.id
            if cropId not in cropProducts:
                cropProducts[cropId] = set()
            cropProducts[cropId].add(trial.product.id)
            productIds.add(trial.product.id)
        # Find categories for products
        productTypes = Product.objects.filter(
            id__in=productIds).values('id', 'type_product')
        productCategories = {item['id']:
<<<<<<< HEAD
                             TrialFilterHelper.productCategory(
            item['category__name'])
            for item in productTypes}
=======
                             Product.getCategory(
                                item['type_product'])
                             for item in productTypes}
>>>>>>> d39a8f1 (change for product type and category)
        counts = {}
        for cropId in cropProducts:
            productsInCrop = cropProducts[cropId]
            counts[cropId] = {'total': 0}
            for productId in productsInCrop:
                category = productCategories[productId]
                if category not in counts[cropId]:
                    counts[cropId][category] = 0
                counts[cropId][category] += 1
                counts[cropId]['total'] += 1
        return counts, len(productIds)

    def getGroupedPlagues(self):
        return Plague.objects.annotate(
            trial_count=Count('fieldtrial'),
            product_count=Count('fieldtrial__product', distinct=True),
            min_date=Min('fieldtrial__initiation_date'),
            max_date=Max('fieldtrial__initiation_date')
        ).values('name', 'id', 'trial_count', 'product_count', 'min_date', 'max_date')

    def generateParamUrl(self):
        params = ''
        for attribute in self._attributes:
            params += f'&{attribute}={self._attributes[attribute]}'
        return params

    @classmethod
    def getCountFieldTrials(cls, product):
        return FieldTrial.objects.filter(product=product).count()

    @staticmethod
    def colorCategory(productCategory):
        return TrialFilterHelper.COLOR_CATEGORY.get(
            productCategory, 'bg-unknown')

    @staticmethod
    def colorProductType(productType):
        category = Product.getCategory(productType)
        return TrialFilterHelper.colorCategory(category)

    def getMinMaxYears(self, param):
        # Step 1: Retrieve the list of items with the date attribute
        items = self._trials.filter(**param)
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
                CROP: ('Crop', 'crops'),
                PLAGUE: ('Plague', 'plagues'),
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
            products.add(item.product.id)
            description = f'{item.crop}'
            if item.plague:
                description += f' + {item.plague}'

            new_list.append({
                'code': item.code,
                'description': description,
                'location': item.location if item.location else '',
                'active_substance': item.product.active_substance,
                'product': item.product,
                'type_product': item.product.nameType(),
                'color_category': TrialFilterHelper.colorProductType(
                    item.product.type_product),
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


class CropListView(LoginRequiredMixin, FilterView):
    model = FieldTrial
    paginate_by = 15  # if pagination is desired
    login_url = '/login'
    template_name = 'baaswebapp/baas_view_list.html'

    def prepareBar(self, productInfo, cropId):
        counts = productInfo.get(cropId, None)
        if not counts:
            vals = {category: 0 for category
                    in TrialFilterHelper.COLOR_CATEGORY}
            return 0, vals
        total = counts['total']
        countCategories = {}
        for category in TrialFilterHelper.COLOR_CATEGORY:
            value = counts.get(category, 0)
            percentage = int(round(value * 100 / total, 0))
            label = category
            countCategories[label] = round(percentage, 0)
        return total, countCategories

    def get_context_data(self, **kwargs):
        new_list = []
        fHelper = TrialFilterHelper(self.request.GET)
        fHelper.filter()
        objectList = fHelper.getClsObjects(Crop).order_by('name')
        num_trials = fHelper.countTrials()
        countCategories = fHelper.countProductCategories()
        graphCategories = ProductCategoryGraph.draw(countCategories)
        trialsPerCrop = fHelper.countBy('crop__name')
        productInfo, totalProducts = fHelper.countProductCategoriesAndCrop()
        for item in objectList:
            tProduct, barValues = self.prepareBar(productInfo, item.id)
            new_list.append({
                'name': item.name,
                'efficacies': '??',
                'date_range': fHelper.getMinMaxYears({'crop': item}),
                'trials': trialsPerCrop.get(item.name, None),
                'products': tProduct,
                'bar_values': barValues,
                'id': item.id})
        return {'object_list': new_list,
                'num_products': totalProducts,
                'trialfilter': fHelper.getFilter(),
                'groupbyfilter': BaaSView.groupByOptions(),
                'groupby': BaaSView.CROP,
                'num_trials': num_trials,
                'graphCategories': graphCategories,
                'extra_params': fHelper.generateParamUrl()}


class PlaguesListView(LoginRequiredMixin, FilterView):
    model = FieldTrial
    paginate_by = 100  # if pagination is desired
    login_url = '/login'
    template_name = 'baaswebapp/baas_view_list.html'

    def get_context_data(self, **kwargs):
        plagues_list = []
        fHelper = TrialFilterHelper(self.request.GET)
        fHelper.filter()
        objectList = fHelper.getTrials().order_by('-code')
        num_trials = fHelper.countTrials()
        countCategories = fHelper.countProductCategories()
        graphCategories = ProductCategoryGraph.draw(countCategories)
        plagues = fHelper.getGroupedPlagues()
        totalProducts = fHelper.countProducts()
        print("TRACE | filterHelper | PlaguesListView | plagues")
        for plague in plagues:
            print(plague)
            minYear = str(
                plague['min_date'].year) if plague['min_date'] is not None else ''
            maxYear = str(
                plague['max_date'].year) if plague['max_date'] is not None else ''
            plagues_list.append(
                {
                    'name': plague['name'],
                    'product_count': plague['product_count'],
                    'trial_count': plague['trial_count'],
                    'id': plague['id'],
                    'progress': (plague['product_count'] * 100) / totalProducts,
                    'date_range': f"{minYear} - {maxYear}"
                }
            )
        return {'object_list': plagues_list,
                'num_products': totalProducts,
                'trialfilter': fHelper.getFilter(),
                'groupbyfilter': BaaSView.groupByOptions(),
                'groupby': BaaSView.PLAGUE,
                'num_trials': num_trials,
                'graphCategories': graphCategories,
                'extra_params': fHelper.generateParamUrl()}
