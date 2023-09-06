from django.db.models import Q, Count, Min, Max
import django_filters
from baaswebapp.models import Category, PType, ModelHelpers
from trialapp.models import FieldTrial, Crop, Plague
from catalogue.models import Product
from django.contrib.auth.mixins import LoginRequiredMixin
from django.views.generic import View
from baaswebapp.graphs import ProductCategoryGraph, COLOR_control, \
    COLOR_estimulant, COLOR_nutritional, COLOR_unknown
from django.shortcuts import redirect, render
from django.urls import reverse
from django.utils.translation import gettext_lazy as _


class TrialFilter(django_filters.FilterSet):
    crop = django_filters.ModelChoiceFilter(
        queryset=Crop.objects.all().order_by('name'),
        empty_label=_('crop').capitalize())
    plague = django_filters.ModelChoiceFilter(
        queryset=Plague.objects.all().order_by('name'),
        empty_label=_('pest / disease').capitalize())
    product__type_product = django_filters.ChoiceFilter(
        choices=PType.choices,
        field_name='product__type_product',
        label='product type',
        empty_label=_('product type').capitalize())

    class Meta:
        model = FieldTrial
        fields = ['crop', 'plague', 'product__type_product']


class TrialFilterHelper:
    _attributes = None
    _trials = None
    _trialFilter = None

    KEY_PER_CLS = {Product: 'product_id',
                   Crop: 'crop_id',
                   Plague: 'plague_id'}

    COLOR_CATEGORY = {
        Category.NUTRITIONAL: 'bg-nutritional',
        Category.ESTIMULANT: 'bg-estimulant',
        Category.CONTROL: 'bg-control',
        Category.UNKNOWN: 'bg-unknown'}
    COLOR_CODE = {
        'bg-nutritional': COLOR_nutritional,
        'bg-estimulant': COLOR_estimulant,
        'bg-control': COLOR_control,
        'bg-unknown': COLOR_unknown}

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
                q_name |= Q(product__active_substance__icontains=paramId)
                q_objects &= q_name
            elif paramIdName in ['product__type_product'] and paramId:
                q_objects &= Q(**({'{}'.format(paramIdName): paramId}))
            elif paramId:
                q_objects &= Q(**({'{}__id'.format(paramIdName): paramId}))
        return q_objects

    def countTrials(self):
        return len(self._trials)

    def graphProductCategories(self):
        countCategories = self.countProductCategories()
        bios = self.countBios()
        return ProductCategoryGraph.draw(countCategories, bios)

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

    def countBios(self):
        bios = self.countBy('product__biological')
        return bios.get(True, 0)

    def countBy(self, param, isDistinct=False):
        counts = self._trials.values(
            param
        ).annotate(
            total=Count('id', distinct=isDistinct)
        ).order_by(param)
        return {item[param]: item['total'] for item in counts}

    def getGroupedPlagues(self):
        return Plague.objects.filter(
                ~Q(name__in=ModelHelpers.THE_UNKNNOWNS)
            ).annotate(
            trial_count=Count('fieldtrial'),
            product_count=Count('fieldtrial__product', distinct=True),
            min_date=Min('fieldtrial__initiation_date'),
            max_date=Max('fieldtrial__initiation_date')
        ).values('name', 'id', 'trial_count', 'product_count',
                 'min_date', 'max_date')

    def countCategoriesPerClass(self, cls):
        classProducts = {}
        productIds = set()
        # Scan products in trials
        for trial in self._trials:
            if cls == Crop:
                itemId = trial.crop.id
            elif cls == Plague:
                if trial.plague and \
                   not ModelHelpers.isInUnknowns(trial.plague.name):
                    itemId = trial.plague.id
                else:
                    continue
            if itemId not in classProducts:
                classProducts[itemId] = set()
            classProducts[itemId].add(trial.product.id)
            productIds.add(trial.product.id)
        # Find categories for products
        productTypes = Product.objects.filter(
            id__in=productIds).values('id', 'type_product')
        productCategories = {item['id']:
                             Product.getCategory(item['type_product'])
                             for item in productTypes}
        counts = {}
        for itemId in classProducts:
            productsInCrop = classProducts[itemId]
            counts[itemId] = {'total': 0}
            for productId in productsInCrop:
                category = productCategories[productId]
                if category not in counts[itemId]:
                    counts[itemId][category] = 0
                counts[itemId][category] += 1
                counts[itemId]['total'] += 1
        return counts, len(productIds)

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

    def getRangeEfficacy(self, param):
        items = self._trials.filter(**param)
        min_efficacy = items.aggregate(
                min_efficacy=Min('best_efficacy'))['min_efficacy']
        max_efficacy = items.aggregate(
                max_efficacy=Max('best_efficacy'))['max_efficacy']

        range_efficacy = '??'
        if min_efficacy:
            range_efficacy = f'{round(min_efficacy, 0)}'
            if min_efficacy != max_efficacy:
                range_efficacy += f' - {round(max_efficacy, 0)}'
            range_efficacy += ' %'
        return range_efficacy


class BaaSView(LoginRequiredMixin, View):
    model = FieldTrial
    paginate_by = 15  # if pagination is desired
    login_url = '/login'
    template_name = 'baaswebapp/baas_view_list.html'
    _fHelper = None

    PRODUCT = 'product'
    CROP = 'crop'
    PLAGUE = 'plague'
    TRIALS = 'trials'
    # value on select : (label on select , url )
    GROUP_BY = {PRODUCT: (_('product'), 'product-list'),
                CROP: (_('crop'), 'crop-list'),
                PLAGUE: (_('pest / disease'), 'plagues-list'),
                TRIALS: (_('Ungrouped'), 'trial-list')}

    def prepareBar(self, itemInfo, itemId):
        counts = itemInfo.get(itemId, None)
        if not counts:
            vals = {category: 0 for category
                    in TrialFilterHelper.COLOR_CATEGORY}
            return 0, vals
        total = counts['total']
        countCategories = {}
        for category in TrialFilterHelper.COLOR_CATEGORY:
            value = counts.get(category, 0)
            percentage = int(round(value * 100 / total, 0))
            # see expected values in product_bar.html
            label = category.label.lower()
            countCategories[label] = round(percentage, 0)
        return total, countCategories

    @staticmethod
    def groupByOptions():
        return [{'value': item, 'name': BaaSView.GROUP_BY[item][0]}
                for item in BaaSView.GROUP_BY]

    def get(self, request, *args, **kwargs):
        groupbyTag = request.GET.get('groupby', None)
        if groupbyTag and groupbyTag != self._groupbyTag:
            redirectTuple = BaaSView.GROUP_BY.get(groupbyTag,
                                                  (0, BaaSView.PRODUCT))
            return redirect(reverse(redirectTuple[1]))

        self._fHelper = TrialFilterHelper(self.request.GET)
        self._fHelper.filter()
        context = self.get_context_data()
        context['trialfilter'] = self._fHelper.getFilter()
        context['groupbyfilter'] = BaaSView.groupByOptions()
        context['extra_params'] = self._fHelper.generateParamUrl()
        context['groupby'] = self._groupbyTag
        context['graphCategories'] = self._fHelper.graphProductCategories()
        context['num_trials'] = self._fHelper.countTrials()
        return render(request, self.template_name, context)


class TrialListView(BaaSView):
    _groupbyTag = BaaSView.TRIALS

    def get_context_data(self, **kwargs):
        new_list = []
        objectList = self._fHelper.getTrials().order_by('-code')
        products = set()
        for item in objectList:
            products.add(item.product.id)
            new_list.append({
                'code': item.code,
                'description': item.getDescription(),
                'location': item.location if item.location else '',
                'active_substance': item.product.active_substance,
                'product': item.product,
                'type_product': item.product.nameType(),
                'biological': item.product.biological,
                'color_category': TrialFilterHelper.colorProductType(
                    item.product.type_product),
                'efficacies': f'{item.best_efficacy} %' if item.best_efficacy
                else '??',
                'period': item.getPeriod(),
                'trials': '',
                'id': item.id})
        return {'object_list': new_list,
                'num_products': len(products)}


class PlaguesListView(BaaSView):
    _groupbyTag = BaaSView.PLAGUE
    model = FieldTrial
    paginate_by = 100  # if pagination is desired
    login_url = '/login'
    template_name = 'baaswebapp/baas_view_list.html'

    def get_context_data(self, **kwargs):
        plagues_list = []
        objectList = self._fHelper.getClsObjects(Plague).order_by('name')
        trialsPerPlague = self._fHelper.countBy('plague__name')
        pInfo, totalProducts = self._fHelper.countCategoriesPerClass(Plague)
        for item in objectList:
            tProduct, barValues = self.prepareBar(pInfo, item.id)
            plagues_list.append({
                'name': item.name,
                'trials': trialsPerPlague.get(item.name, None),
                'id': item.id,
                'products': tProduct,
                'bar_values': barValues,
                'efficacies': self._fHelper.getRangeEfficacy({'plague': item}),
                'date_range': self._fHelper.getMinMaxYears({'plague': item})
                })
        return {'object_list': plagues_list,
                'num_products': totalProducts}


class CropListView(BaaSView):
    _groupbyTag = BaaSView.CROP

    def get_context_data(self, **kwargs):
        new_list = []
        objectList = self._fHelper.getClsObjects(Crop).order_by('name')
        trialsPerCrop = self._fHelper.countBy('crop__name')
        prodInfo, totalProducts = self._fHelper.countCategoriesPerClass(Crop)
        for item in objectList:
            tProduct, barValues = self.prepareBar(prodInfo, item.id)
            new_list.append({
                'name': item.name,
                'efficacies': self._fHelper.getRangeEfficacy({'crop': item}),
                'date_range': self._fHelper.getMinMaxYears({'crop': item}),
                'trials': trialsPerCrop.get(item.name, None),
                'products': tProduct,
                'bar_values': barValues,
                'id': item.id})
        return {'object_list': new_list,
                'num_products': totalProducts}


class ProductListView(BaaSView):
    _groupbyTag = BaaSView.PRODUCT

    def get_context_data(self, **kwargs):
        new_list = []
        objectList = self._fHelper.getClsObjects(Product).order_by(
            'vendor__id', 'name')
        trialsPerProduct = self._fHelper.countBy('product__name')
        for item in objectList:
            new_list.append({
                'name': item.name,
                'active_substance': item.active_substance,
                'type_product': item.nameType(),
                'biological': item.biological,
                'color_category': TrialFilterHelper.colorProductType(
                    item.type_product),
                'efficacies': self._fHelper.getRangeEfficacy(
                    {'product': item}),
                'date_range': self._fHelper.getMinMaxYears({'product': item}),
                'trials': trialsPerProduct.get(item.name, None),
                'id': item.id})
        return {'object_list': new_list,
                'num_products': len(objectList)}
