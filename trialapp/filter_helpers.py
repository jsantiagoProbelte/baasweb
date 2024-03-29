from django.db.models import Q, Count, Min, Max
import django_filters
from baaswebapp.models import Category, PType, ModelHelpers
from trialapp.models import FieldTrial, Crop, Plague, StatusTrial, Objective, \
    TrialType
from catalogue.models import Product
from django.contrib.auth.mixins import LoginRequiredMixin
from django.views.generic import View
from baaswebapp.graphs import ProductCategoryGraph, COLOR_control, \
    COLOR_estimulant, COLOR_nutritional, COLOR_unknown
from django.shortcuts import redirect, render
from django.urls import reverse
from django.utils.translation import gettext_lazy as _
from django.core.paginator import Paginator
from trialapp.trial_helper import TrialPermission


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


class TrialFilterExtended(django_filters.FilterSet):
    name = django_filters.CharFilter(lookup_expr='icontains')
    status_trial = django_filters.ChoiceFilter(
        choices=StatusTrial.choices,
        field_name='status_trial',
        label='status',
        empty_label=_('Status').capitalize())
    trial_type = django_filters.ModelChoiceFilter(
        queryset=TrialType.objects.all().order_by('name'),
        label=_("type").capitalize(),
        empty_label=_("type").capitalize())
    objective = django_filters.ModelChoiceFilter(
        queryset=Objective.objects.all().order_by('name'),
        label=_("objective").capitalize(),
        empty_label=_("objective").capitalize())
    product = django_filters.ModelChoiceFilter(
        queryset=Product.objects.all().order_by('name'),
        label=_("product").capitalize(),
        empty_label=_("product").capitalize())
    crop = django_filters.ModelChoiceFilter(
        queryset=Crop.objects.all().order_by('name'),
        label=_("crop").capitalize(),
        empty_label=_("crop").capitalize())
    plague = django_filters.ModelChoiceFilter(
        queryset=Plague.objects.all().order_by('name'),
        label=_("pest / disease").capitalize(),
        empty_label=_("pest / disease").capitalize()
        )
    product__type_product = django_filters.ChoiceFilter(
        field_name="product__type_product",
        choices=PType.choices,
        label=_("Product Type"),
        empty_label=_("Product Type")
    )

    class Meta:
        model = FieldTrial
        fields = ['name', 'status_trial', 'trial_type', 'objective',
                  'crop', 'plague', 'product', 'product__type_product']


class TrialFilterHelper:
    _attributes = None
    _trials = None
    _trialFilter = None
    _permisions = None
    _userName = None

    PRODUCT = 'product'
    CROP = 'crop'
    PLAGUE = 'plague'
    TRIALS = 'trials'

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
    def __init__(self, request, extra_attribute=None):
        self.setTrialFilter(request.GET, extra_attribute)
        self._permisions = TrialPermission(None, request.user)
        self._userName = request.user.username

    def setTrialFilter(self, attributes, extra_attribute=None):
        # Take of remove empty values
        self._attributes = {}
        for key in attributes:
            value = attributes.get(key, None)
            if value:
                self._attributes[key] = value
        if extra_attribute:
            for key in extra_attribute:
                self._attributes[key] = extra_attribute[key]
        self._trialFilter = TrialFilter(self._attributes)

    def getFilter(self):
        return self._trialFilter

    def filter(self, groupbyTag=None):
        q_objects = self.prepareFilter(groupbyTag=groupbyTag)
        self.filterTrials(q_objects)

    def getTrials(self):
        return self._trials

    def getClsObjects(self, cls):
        if self._permisions._type != TrialPermission.ADMIN:
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

    def addTrialPermisionsToFilter(self, q_objects):
        q_discover = Q()
        if self._permisions._type == TrialPermission.ADMIN:
            pass
        elif self._permisions._type == TrialPermission.INTERNAL:
            q_discover |= Q(status_trial=StatusTrial.DONE)
            q_discover |= Q(responsible=self._userName)
        elif self._permisions._type == TrialPermission.EXTERNAL:
            q_discover |= Q(public=True)
            q_discover |= Q(responsible=self._userName)
        return q_discover

    TAKEITASITIS = ['product__type_product', 'status_trial']

    def prepareFilter(self, groupbyTag=None):
        paramsReplyTemplate = TrialFilter.Meta.fields + ['name'] + \
            TrialFilterExtended.Meta.fields
        q_objects = Q(trial_meta=FieldTrial.TrialMeta.FIELD_TRIAL)
        for paramIdName in paramsReplyTemplate:
            paramId = self.getAttrValue(paramIdName)
            if paramIdName == 'name' and paramId:
                q_name = Q()
                q_name |= Q(name__icontains=paramId)
                q_name |= Q(responsible__icontains=paramId)
                q_name |= Q(plague__other__icontains=paramId)
                q_name |= Q(plague__name__icontains=paramId)
                q_name |= Q(code__icontains=paramId)
                q_name |= Q(product__active_substance__icontains=paramId)
                q_objects &= q_name
            elif paramIdName in TrialFilterHelper.TAKEITASITIS and paramId:
                q_objects &= Q(**({'{}'.format(paramIdName): paramId}))
            elif paramId:
                q_objects &= Q(**({'{}__id'.format(paramIdName): paramId}))
            elif groupbyTag == TrialFilterHelper.PLAGUE:
                # En este caso estamos en la vista de plagues, filtramos los
                # ensayos que no referencien a plagues
                q_objects &= ~Q(plague__name__in=ModelHelpers.THE_UNKNNOWNS)

        # add restrictions based on type of user
        q_objects &= self.addTrialPermisionsToFilter(q_objects)
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
        counts = self.getTrials().values(
            param
        ).annotate(
            total=Count('id', distinct=isDistinct)
        ).order_by(param)
        return {item[param]: item['total'] for item in counts}

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
    paginate_by = 10  # if pagination is desired
    login_url = '/login'
    template_name = 'baaswebapp/baas_view_list.html'
    _fHelper = None

    # value on select : (label on select , url )
    GROUP_BY = {TrialFilterHelper.PRODUCT: (_('product'), 'product-list'),
                TrialFilterHelper.CROP: (_('crop'), 'crop-list'),
                TrialFilterHelper.PLAGUE: (_('pest / disease'),
                                           'plagues-list'),
                TrialFilterHelper.TRIALS: (_('Ungrouped'), 'trial-list')}

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
            redirectTuple = BaaSView.GROUP_BY.get(
                groupbyTag, (0, TrialFilterHelper.PRODUCT))
            return redirect(reverse(redirectTuple[1]))

        page = request.GET.get('page', 1)
        self._fHelper = TrialFilterHelper(self.request)
        self._fHelper.filter(groupbyTag=self._groupbyTag)

        # pagination
        allItems = self.get_context_data()
        paginator = Paginator(allItems, BaaSView.paginate_by)
        currentPage = paginator.get_page(page)

        context = {
            'trialfilter': self._fHelper.getFilter(),
            'groupbyfilter': BaaSView.groupByOptions(),
            'extra_params': self._fHelper.generateParamUrl(),
            'groupby': self._groupbyTag,
            'graphCategories': self._fHelper.graphProductCategories(),
            'num_trials': self._fHelper.countTrials(),
            'page': currentPage,
            'paginator': paginator,
            **self.prepareItems(currentPage.object_list)}
        return render(request, self.template_name, context)


class TrialListView(BaaSView):
    _groupbyTag = TrialFilterHelper.TRIALS

    def get_context_data(self, **kwargs):
        return self._fHelper.getTrials().order_by('-code')

    def prepareItems(self, objectList):
        new_list = []
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
    _groupbyTag = TrialFilterHelper.PLAGUE
    model = FieldTrial
    paginate_by = 100  # if pagination is desired
    login_url = '/login'
    template_name = 'baaswebapp/baas_view_list.html'

    def getSizeOfTrials(self, trialObj):
        return trialObj["trials"] if trialObj["trials"] is not None else 0

    def get_context_data(self, **kwargs):
        return self._fHelper.getClsObjects(Plague)\
            .annotate(trials=Count('fieldtrial')).order_by('-trials')

    def prepareItems(self, objectList):
        new_list = []
        pInfo, totalProducts = self._fHelper.countCategoriesPerClass(Plague)
        trialsPerPlague = self._fHelper.countBy('plague__name')
        for item in objectList:
            tProduct, barValues = self.prepareBar(pInfo, item.id)
            new_list.append({
                'name': item.name,
                'trials': trialsPerPlague.get(item.name, None),
                'id': item.id,
                'products': tProduct,
                'bar_values': barValues,
                'efficacies': self._fHelper.getRangeEfficacy({'plague': item}),
                'date_range': self._fHelper.getMinMaxYears({'plague': item})
                })
        new_list.sort(reverse=True,
                      key=self.getSizeOfTrials)
        return {'object_list': new_list,
                'num_products': totalProducts}


class CropListView(BaaSView):
    _groupbyTag = TrialFilterHelper.CROP

    def get_context_data(self, **kwargs):
        return self._fHelper.getClsObjects(Crop)\
            .annotate(trials=Count('fieldtrial')).order_by('-trials')

    def getSizeOfTrials(self, trialObj):
        return trialObj["trials"] if trialObj["trials"] is not None else 0

    def prepareItems(self, objectList):
        new_list = []
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
        new_list.sort(reverse=True,
                      key=self.getSizeOfTrials)
        return {'object_list': new_list,
                'num_products': totalProducts}


class ProductListView(BaaSView):
    _groupbyTag = TrialFilterHelper.PRODUCT

    def get_context_data(self, **kwargs):
        return self._fHelper.getClsObjects(Product)\
            .annotate(trials=Count('fieldtrial')).order_by('-trials')

    def getSizeOfTrials(self, trialObj):
        return trialObj["trials"] if trialObj["trials"] is not None else 0

    def prepareItems(self, objectList):
        new_list = []
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
                'trials': item.trials,
                'id': item.id})
        new_list.sort(reverse=True,
                      key=self.getSizeOfTrials)
        return {'object_list': new_list,
                'num_products': len(objectList)}


class DetailedTrialListView:
    _request = None
    _trialFilter = None
    _paginate_by = None

    def __init__(self, request, paginate_by=7,
                 extra_params=None):
        self._request = request
        self._paginate_by = paginate_by
        self._trialFilter = TrialFilterHelper(self._request,
                                              extra_params)

    def filterTrials(self):
        self._trialFilter.filter(groupbyTag=TrialFilterHelper.TRIALS)
        return self._trialFilter.getTrials().order_by('-code')

    def mindTheZero(self, value):
        if value == 0:
            return '0'
        else:
            return value

    def displayTrial(self, trial):
        return {
            'code': trial.code,
            'temp_avg': self.mindTheZero(trial.avg_temperature),
            'prep_avg': self.mindTheZero(trial.avg_precipitation),
            'hum_avg': self.mindTheZero(trial.avg_humidity),
            'description': trial.getDescription(),
            'location': trial.getLocation(showNothing=True),
            'goal': trial.objective,
            'crop': trial.crop.name,
            'best_efficacy': trial.getBestEfficacy(),
            'product': trial.product.name,
            'period': trial.getPeriod(),
            'cultivation': trial.getCultivation(),
            'status_trial': trial.get_status_trial_display(),
            'objective': trial.objective.name,
            'plague': trial.plague.name if trial.plague else '',
            'latitude': trial.latitude,
            'longitude': trial.longitude,
            'id': trial.id,
            'initiation_date': trial.initiation_date}

    def getGraph(self):
        return self._trialFilter.graphProductCategories()

    def getTrials(self):
        page = self._request.GET.get('page', 1)
        allTrials = self.filterTrials()
        products = set()
        for trial in allTrials:
            products.add(trial.product.id)

        paginator = Paginator(allTrials, self._paginate_by)
        pageTrials = [self.displayTrial(trial) for trial in
                      paginator.get_page(page).object_list]

        return {
            'trial_list': pageTrials,
            'show_status': True if self._request.user.is_staff else False,
            'filter': TrialFilterExtended(self._request.GET),
            'paginator': paginator,
            'page': paginator.get_page(page),
            'num_products': len(products),
            'num_trials': len(allTrials)}
