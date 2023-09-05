from django.contrib.auth.mixins import LoginRequiredMixin
from django.views import View
import django_filters
from baaswebapp.models import RateTypeUnit
from django.db.models import Count, Min, Max
from catalogue.models import Product, Batch, Treatment, ProductVariant, \
    Vendor
from trialapp.models import Crop, Objective, Plague, TreatmentThesis, \
    FieldTrial, TrialStatus, TrialType
from trialapp.data_models import ThesisData, DataModel, ReplicaData, \
    Assessment
from trialapp.filter_helpers import TrialFilterHelper
from django.shortcuts import render, get_object_or_404
from rest_framework.views import APIView
from baaswebapp.graphs import GraphTrial
from django.views.generic.edit import CreateView, UpdateView, DeleteView
from django.utils.translation import gettext_lazy as _
from crispy_forms.helper import FormHelper
from django.urls import reverse_lazy
from crispy_forms.layout import Layout, Div, Submit, Field, HTML
from crispy_forms.bootstrap import FormActions
from django import forms
from django.http import HttpResponseRedirect
from trialapp.data_views import DataGraphFactory
from django.core.paginator import Paginator
from django.urls import reverse


class ProductFormLayout(FormHelper):
    def __init__(self, new=True):
        super().__init__()
        title = 'New product' if new else 'Edit product'
        submitTxt = 'Create' if new else 'Save'
        self.add_layout(Layout(Div(
            HTML(title), css_class="h4 mt-4"),
            Div(Field('name', css_class='mb-3'),
                Field('active_substance', css_class='mb-3'),
                Field('vendor', css_class='mb-3'),
                Field('type_product', css_class='mb-3'),
                Field('biological', css_class='mb-3'),
                FormActions(
                    Submit('submit', submitTxt, css_class="btn btn-info"),
                    css_class='text-sm-end'),
                css_class="card-body-baas mt-2")))


class TrialProductFilter(django_filters.FilterSet):
    name = django_filters.CharFilter(lookup_expr='icontains')
    trial_status = django_filters.ModelChoiceFilter(
        queryset=TrialStatus.objects.all().order_by('name'),
        empty_label=_("Status"))
    trial_type = django_filters.ModelChoiceFilter(
        queryset=TrialType.objects.all().order_by('name'),
        empty_label=_("Type"))
    objective = django_filters.ModelChoiceFilter(
        queryset=Objective.objects.all().order_by('name'),
        empty_label=_("Objective"))
    crop = django_filters.ModelChoiceFilter(
        queryset=Crop.objects.all().order_by('name'), empty_label=_("Crop"))
    plague = django_filters.ModelChoiceFilter(
        queryset=Plague.objects.all().order_by('name'),
        empty_label=_("Plague"))

    class Meta:
        model = FieldTrial
        fields = ['trial_status', 'trial_type', 'objective',
                  'crop', 'plague']


class TrialProductFilterHelper:
    _attributes = None
    _trialsByProduct = None
    _currentFilter = None
    _productId = None

    def __init__(self, attributes, productId):
        self.putInitVariables(productId=productId)
        self.readAttributes(attributes)

    def putInitVariables(self, **kwargs):
        self._productId = kwargs["productId"]
        self._attributes = {}

    def readAttributes(self, attributes):
        for key in attributes:
            value = attributes.get(key, None)
            if value:
                self._attributes[key] = value

    def getFieldTrialsByFilter(self, attributes):
        new_list = []
        trialsFiltered = []
        if not self._trialsByProduct:
            self._trialsByProduct = FieldTrial.objects.filter(
                product_id=self._productId)

        trialsFiltered = self._trialsByProduct
        if attributes.get('crop'):
            trialsFiltered = trialsFiltered.filter(crop=attributes.get('crop'))
        if attributes.get('plague'):
            trialsFiltered = trialsFiltered.filter(
                plague=attributes.get('plague'))
        if attributes.get('trial_status'):
            trialsFiltered = trialsFiltered.filter(
                trial_status=attributes.get('trial_status'))
        if attributes.get('name'):
            trialsFiltered = trialsFiltered.filter(
                name__icontains=attributes.get('name'))

        trialsFiltered = trialsFiltered.annotate(
            assessments=Count('assessment')).order_by('-code', 'name')
        thesisCounts = trialsFiltered.annotate(
            thesiss=Count('thesis'))
        thesisCountDict = {item.id: item.thesiss for item in thesisCounts}

        for item in trialsFiltered:
            cultivation = item.cultivation if item.cultivation else '-'
            cultivation += '<br>'
            cultivation += item.irrigation if item.irrigation else '-'
            cultivation += '<br>'
            cultivation += item.soil if item.soil else '-'
            new_list.append({
                'code': item.code,
                'name': item.name,
                'crop': item.crop.name,
                'best_efficacy': f'{item.best_efficacy}%' if item.best_efficacy
                else '??',
                'product': item.product.name,
                'cultivation': cultivation,
                'trial_status': item.trial_status if item.trial_status else '',
                'objective': item.objective.name,
                'plague': item.plague.name if item.plague else '',
                'latitude': item.latitude,
                'longitude': item.longitude,
                'id': item.id,
                'assessments': item.assessments,
                'initiation_date': item.initiation_date,
                'thesis': thesisCountDict.get(item.id, 0)})
        return new_list


class ProductForm(forms.ModelForm):
    class Meta:
        model = Product
        fields = ('name', 'vendor', 'active_substance',
                  'type_product', 'biological')

    def __init__(self, *args, **kwargs):
        super(ProductForm, self).__init__(*args, **kwargs)
        vendors = Vendor.objects.all().order_by('name')
        self.fields['vendor'].queryset = vendors
        self.fields['active_substance'].required = False


class ProductCreateView(LoginRequiredMixin, CreateView):
    model = Product
    form_class = ProductForm
    template_name = 'baaswebapp/model_edit_form.html'

    def get_form(self, form_class=ProductForm):
        form = super().get_form(form_class)
        form.helper = ProductFormLayout()
        return form

    def form_valid(self, form):
        if form.is_valid():
            item = form.instance
            item.save()

            # Let's create default variant and default batch
            variant = ProductVariant.createDefault(item)
            Batch.createDefault(variant)
            return HttpResponseRedirect(item.get_absolute_url())


class ProductUpdateView(LoginRequiredMixin, UpdateView):
    model = Product
    form_class = ProductForm
    template_name = 'baaswebapp/model_edit_form.html'

    def get_form(self, form_class=ProductForm):
        form = super().get_form(form_class)
        form.helper = ProductFormLayout(new=False)
        return form


class ProductDeleteView(DeleteView):
    model = Product
    success_url = reverse_lazy('product-list')
    template_name = 'catalogue/product_delete.html'


class ProductApi(LoginRequiredMixin, View):
    TAG_DIMENSIONS = 'dimensions'
    TAG_CROPS = 'crops'
    TAG_PLAGUES = 'plagues'
    TAG_LEVEL = 'level'
    FILTER_DATA = [TAG_CROPS, TAG_DIMENSIONS, TAG_PLAGUES, TAG_LEVEL]

    def identifyObjectFilter(self, tags):
        dimensions = []
        crops = []
        plagues = []
        level = GraphTrial.L_REPLICA
        for tag in tags:
            if tag in ProductApi.FILTER_DATA:
                tagId = tags[tag]
                if tagId == 'None' or tagId == '':
                    continue
                if tag == ProductApi.TAG_CROPS:
                    crops.append(Crop.objects.get(pk=tagId))
                if tag == ProductApi.TAG_DIMENSIONS:
                    dimensions.append(RateTypeUnit.objects.get(pk=tagId))
                if tag == ProductApi.TAG_PLAGUES:
                    plagues.append(Plague.objects.get(pk=tagId))
                if tag == ProductApi.TAG_LEVEL:
                    if tagId == GraphTrial.L_THESIS:
                        level = GraphTrial.L_THESIS
                    elif tagId == GraphTrial.L_REPLICA:
                        level = GraphTrial.L_REPLICA
        return dimensions, crops, plagues, level

    def calcularGraphs(self, product, tags, graphPerRow=2):
        if 'show_data' not in tags:
            return [], '', 'col-md-12'
        dimensions, crops, plagues, level = self.identifyObjectFilter(tags)
        classGroup = GraphTrial.classColGraphs(len(crops), graphPerRow)
        if len(crops) == 0:
            return [], 'Please select crop', classGroup

        if len(dimensions) == 0:
            # Use all available dimensions
            dimensions = DataModel.dimensionsValues(product, as_array=False)

        croplagues = []
        for crop in crops:
            if len(plagues) > 0:
                for plague in plagues:
                    croplagues.append([crop, plague])
            else:
                croplagues.append([crop, None])

        graphs = []
        notFound = ''

        for dimension in dimensions:
            graphDim = self.fetchData(product, dimension,
                                      croplagues, graphPerRow,
                                      level)
            if len(graphDim['values']):
                graphs.append(graphDim)
            else:
                notFound += dimension.getName() + ', '
        if len(notFound) > 0:
            textNotFound = '<div class="alert alert-warning" role="alert">'\
                           'Data not found for ' + notFound + ' dimensions.'\
                           '</div>'
            graphs.append(
                {'name': 'Not Found',
                 'values': [[{'name': 'Not Found', 'graph': textNotFound}]]})
        return graphs, '', classGroup

    def fetchData(self, product, dimension, croplagues,
                  graphPerRow, level):
        graphDim = {'name': "{}".format(dimension.getName()),
                    'values': []}
        lastRow = []
        for croplague in croplagues:
            # Get graph
            crop = croplague[0]
            plague = croplague[1]
            nameItem = crop.name
            if plague:
                nameItem += '-' + plague.name

            ratedParts = Assessment.getRatedPartsProduct(
                product, crop, plague, dimension)

            for ratedPart in ratedParts:
                if ratedPart:
                    nameItem += '-' + ratedPart
                graph, fieldTrials = self.computeGraph(
                    product, crop, plague, dimension, level, ratedPart)
                if graph:
                    item = {'name': nameItem, 'graph': graph,
                            'trials': fieldTrials}
                    lastRow.append(item)
                    if len(lastRow) > graphPerRow:
                        graphDim['values'].append(lastRow)
                        lastRow = []

        if len(lastRow) > 0:
            graphDim['values'].append(lastRow)

        return graphDim

    def computeGraph(self, product, crop, plague,
                     rateType, level, ratedPart):
        assmnts, fieldTrials, thesis = DataModel.getDataPointsProduct(
            product, crop, plague, rateType, ratedPart)

        if assmnts:
            assIds = [item.id for item in assmnts]
        dataPoints = None
        # Fetch Data
        if level == GraphTrial.L_THESIS:
            dataPoints = ThesisData.dataPointsAssess(assIds)
        elif level == GraphTrial.L_REPLICA:
            dataPoints = ReplicaData.dataPointsAssess(assIds)

        if dataPoints:
            graphT = DataGraphFactory(level, assmnts, dataPoints,
                                      xAxis=GraphTrial.L_DAF,
                                      references=thesis)
            return graphT.draw(), fieldTrials
        else:
            return None, None

    def getProductTree(self, product):
        data = []
        for variant in ProductVariant.getItems(product):
            variantItem = {'name': variant.name, 'id': variant.id,
                           'batches': []}
            for batch in Batch.objects.filter(
                    product_variant=variant).order_by('name'):
                batchItem = {'name': batch.name,
                             'id': batch.id, 'treatments': []}
                for treatment in Treatment.objects.filter(
                                 batch=batch).order_by('name', 'rate'):
                    batchItem['treatments'].append(
                        {'name': treatment.getName(), 'id': treatment.id})
                variantItem['batches'].append(batchItem)
            data.append(variantItem)
        return data

    def filterData(self, filterValues, product):
        filterData = []
        titleGraph = ''
        for tag in ProductApi.FILTER_DATA:
            current = filterValues.get(tag, '')
            currentValue = ''
            values = None
            if tag == ProductApi.TAG_CROPS:
                values = DataModel.getCrops(product)
                if current != '':
                    currentValue = Crop.objects.get(id=current).getName()
            elif tag == ProductApi.TAG_PLAGUES:
                values = DataModel.getPlagues(product)
                if current != '':
                    currentValue = Plague.objects.get(id=current).getName()
            elif tag == ProductApi.TAG_DIMENSIONS:
                values = DataModel.dimensionsValues(product)
                if current != '':
                    currentValue = RateTypeUnit.objects.get(
                        id=current).getName()
            if values:
                filterData.append({
                    'name': tag,
                    'current': int(current) if current != '' else '',
                    'values': values})
            if currentValue != '':
                titleGraph += currentValue + ' - '

        return filterData, titleGraph

    def get_crop_table_data(self, id):
        crops = Crop.objects.filter(fieldtrial__product_id=id).values(
            "id", "name", "fieldtrial__name", "fieldtrial__id",
            "fieldtrial__plague__name", "fieldtrial__samples_per_replica"
        )
        cropsTable = {}

        for crop in crops:
            cropName = crop["name"]
            if cropName in cropsTable:
                cropsTable[cropName]["trials"].append(
                    {"name": crop["fieldtrial__name"],
                     "id": crop["fieldtrial__id"]})
                cropsTable[cropName]["trialsCount"] += 1

                if 'fieldtrial__plague__name' in crop and\
                   crop['fieldtrial__plague__name']:
                    cropsTable[cropName]["agents"].add(
                        crop['fieldtrial__plague__name'])
                    cropsTable[cropName]["strAgents"] = ', '.join(
                        cropsTable[cropName]["agents"])

                cropsTable[cropName]["samples"] += crop[
                    "fieldtrial__samples_per_replica"]
            else:
                cropsTable[cropName] = {"trials": [], "trialsCount": 0,
                                        "name": crop["name"],
                                        "id": crop["id"], "agents": set(),
                                        "strAgents": "", "samples": 0}
                cropsTable[cropName]["trials"].append(
                    {"name": crop["fieldtrial__name"],
                     "id": crop["fieldtrial__id"]})
                cropsTable[cropName]["trialsCount"] += 1
                cropsTable[cropName]["agents"].add(
                    crop['fieldtrial__plague__name'])
                cropsTable[cropName]["samples"] += crop[
                    "fieldtrial__samples_per_replica"]

                if 'fieldtrial__plague__name' in crop and\
                   crop['fieldtrial__plague__name']:
                    cropsTable[cropName]["agents"].add(
                        crop['fieldtrial__plague__name'])
                    cropsTable[cropName]["strAgents"] = ', '.join(
                        cropsTable[cropName]["agents"])
        return cropsTable.values()

    def getRangeEfficacy(self, product):
        trials = FieldTrial.objects.filter(product=product)
        min_efficacy = trials.aggregate(
                min_efficacy=Min('best_efficacy'))['min_efficacy']
        max_efficacy = trials.aggregate(
                max_efficacy=Max('best_efficacy'))['max_efficacy']

        range_efficacy = '??'
        if min_efficacy:
            range_efficacy = f'{round(min_efficacy, 0)}'
            if min_efficacy != max_efficacy:
                range_efficacy += f' - {round(max_efficacy, 0)}'
            range_efficacy += ' %'
        return range_efficacy

    def get(self, request, *args, **kwargs):
        itemsPerPage = 5
        if request.GET.get('activeTab'):
            activeTab = request.GET.get('activeTab')
        else:
            activeTab = "1"
        page = request.GET.get('page') if request.GET.get('page') else 1

        product_id = None
        product_id = kwargs['pk']
        template_name = 'catalogue/product_show.html'
        product = get_object_or_404(Product, pk=product_id)
        filterData, titleGraph = self.filterData(request.GET, product)
        graphs, errorgraphs, classGraphCol = self.calcularGraphs(product,
                                                                 request.GET)
        tpFilter = TrialProductFilterHelper(request.GET, product_id)
        filterTrials = tpFilter.getFieldTrialsByFilter(request.GET)
        paginator = Paginator(filterTrials, itemsPerPage)
        # print(f"TRACE | ProductView | get | paginator ->
        # {paginator.num_pages}")

        currentPage = paginator.get_page(page)

        numTrials = TrialFilterHelper.getCountFieldTrials(product)
        filterTrial = TrialProductFilter(request.GET)
        range_efficacy = self.getRangeEfficacy(product)

        return render(
            request, template_name, {
                'product': product,
                'deleteProductForm': ProductDeleteView(),
                'fieldtrials': numTrials,
                'filterData': filterData,
                'titleGraph': titleGraph,
                'range_efficacy': range_efficacy,
                'graphs': graphs,
                'variants': self.getProductTree(product),
                'errors': errorgraphs,
                'classGraphCol': classGraphCol,
                'titleView': product.getName(),
                'crops': self.get_crop_table_data(product_id),
                'category': product.getCategory(product.type_product).label,
                'trials': currentPage.object_list,
                'paginator': paginator,
                'filter': filterTrial,
                'activeTab': activeTab,
                'page': currentPage})


##############################
# BATCH
class BatchApi(APIView):
    authentication_classes = []
    permission_classes = []
    http_method_names = ['get']

    def get(self, request, *args, **kwargs):
        itemId = kwargs['pk']
        template_name = 'catalogue/catalogue_model_show.html'
        item = get_object_or_404(Batch, pk=itemId)
        product = item.product_variant.product
        subtitle = 'batch'
        values = [{'name': 'name', 'value': item.name},
                  {'name': 'Variant', 'value': item.product_variant},
                  {'name': 'Serial Number', 'value': item.serial_number},
                  {'name': 'rate & unit',
                   'value': '{} {}'.format(item.rate, item.rate_unit)}]

        return renderCatalogue(
            request, product, item, values, subtitle,
            Treatment, 'treatment', 'rate',
            template_name)


class BatchFormLayout(FormHelper):
    def __init__(self, new=True):
        super().__init__()
        title = 'New batch' if new else 'Update batch'
        submitTxt = 'Create' if new else 'Save'
        self.add_layout(Layout(Div(
            HTML(title), css_class="h4 mt-4"),
            Div(
                Field('name', css_class='mb-3'),
                Field('product_variant', css_class='mb-3'),
                Field('serial_number', css_class='mb-3'),
                Field('rate', css_class='mb-3'),
                Field('rate_unit', css_class='mb-3'),
                FormActions(
                    Submit('submit', submitTxt, css_class="btn btn-info"),
                    css_class='text-sm-end'),
                css_class="card-body-baas mt-2")
        ))


class BatchForm(forms.ModelForm):
    class Meta:
        model = Batch
        fields = ['name', 'serial_number', 'rate', 'rate_unit']

    def __init__(self, *args, **kwargs):
        super(BatchForm, self).__init__(*args, **kwargs)
        self.fields['serial_number'].required = False


class BatchCreateView(LoginRequiredMixin, CreateView):
    form_class = BatchForm
    template_name = 'baaswebapp/model_edit_form.html'
    model = Batch

    def get_form(self, form_class=BatchForm):
        form = super().get_form(form_class)
        form.helper = BatchFormLayout()
        return form

    def form_valid(self, form):
        if form.is_valid():
            item = form.instance
            item.product_variant_id = self.kwargs["reference_id"]
            item.save()

            variant = ProductVariant.objects.get(id=item.product_variant_id)
            return HttpResponseRedirect(variant.get_absolute_url())


class BatchUpdateView(LoginRequiredMixin, UpdateView):
    model = Batch
    form_class = BatchForm
    template_name = 'baaswebapp/model_edit_form.html'

    def get_form(self, form_class=BatchForm):
        form = super().get_form(form_class)
        form.helper = BatchFormLayout(new=False)
        return form


class BatchDeleteView(DeleteView):
    model = Batch
    template_name = 'catalogue/batch_delete.html'
    _parent = None

    def delete(self, request, *args, **kwargs):
        self.object = self.get_object()
        self._parent = self.object.product_variant
        self.object.delete()
        return HttpResponseRedirect(self.get_success_url())

    def get_success_url(self):
        if self._parent:
            return reverse('product_variant-api',
                           kwargs={'pk': self._parent.id})
        else:
            return reverse('product-list')


def prepareChildrenCatalogue(childKey, cls, filter, orderBy):
    items = cls.objects.filter(**filter).order_by(orderBy)
    children = [{'id': item.id, 'name': item.getName()} for item in items]
    return {
        'children': children,
        'children_title': _(childKey),
        'children_url': childKey + '-api',
        'children_url_add': childKey + '-add'}


def renderCatalogue(request, product, item, values, subtitle,
                    childCls, childType, orderChild,
                    template_name):
    childrenInfo = prepareChildrenCatalogue(childType, childCls,
                                            {subtitle: item},
                                            orderChild)
    context = {'product': product, 'item': item,
               'values': values, 'subtitle': subtitle,
               'update_url': subtitle + '-update',
               'delete_url': subtitle + '-delete'}

    return render(request, template_name, {**context, **childrenInfo})


##############################
# ProductVariant
class ProductVariantApi(APIView):
    authentication_classes = []
    permission_classes = []
    http_method_names = ['get']

    def get(self, request, *args, **kwargs):
        itemId = kwargs['pk']
        template_name = 'catalogue/catalogue_model_show.html'
        item = get_object_or_404(ProductVariant, pk=itemId)
        product = item.product
        subtitle = 'product_variant'
        values = [{'name': 'name', 'value': item.name},
                  {'name': 'description', 'value': item.description}]

        return renderCatalogue(
            request, product, item, values, subtitle,
            Batch, 'batch', 'name',
            template_name)


class ProductVariantFormLayout(FormHelper):
    def __init__(self, new=True):
        super().__init__()
        title = 'New ProductVariant' if new else 'Update ProductVariant'
        submitTxt = 'Create' if new else 'Save'
        self.add_layout(Layout(Div(
            HTML(title), css_class="h4 mt-4"),
            Div(
                Field('name', css_class='mb-3'),
                Field('description', css_class='mb-3'),
                FormActions(
                    Submit('submit', submitTxt, css_class="btn btn-info"),
                    css_class='text-sm-end'),
                css_class="card-body-baas mt-2")
        ))


class ProductVariantForm(forms.ModelForm):
    class Meta:
        model = ProductVariant
        fields = ['name', 'description']

    def __init__(self, *args, **kwargs):
        super(ProductVariantForm, self).__init__(*args, **kwargs)
        self.fields['description'].required = False


class ProductVariantCreateView(LoginRequiredMixin, CreateView):
    model = ProductVariant
    form_class = ProductVariantForm
    template_name = 'baaswebapp/model_edit_form.html'

    def get_form(self, form_class=ProductVariantForm):
        form = super().get_form(form_class)
        form.helper = ProductVariantFormLayout()
        return form

    def form_valid(self, form):
        if form.is_valid():
            item = form.instance
            item.product_id = self.kwargs["reference_id"]
            item.save()
            Batch.createDefault(item)
            return HttpResponseRedirect(item.product.get_absolute_url())


class ProductVariantUpdateView(LoginRequiredMixin, UpdateView):
    model = ProductVariant
    form_class = ProductVariantForm
    template_name = 'baaswebapp/model_edit_form.html'

    def get_form(self, form_class=ProductVariantForm):
        form = super().get_form(form_class)
        form.helper = ProductVariantFormLayout(new=False)
        return form


class ProductVariantDeleteView(DeleteView):
    model = ProductVariant
    template_name = 'catalogue/product_variant_delete.html'
    _parent = None

    def delete(self, request, *args, **kwargs):
        self.object = self.get_object()
        self._parent = self.object.product
        self.object.delete()
        return HttpResponseRedirect(self.get_success_url())

    def get_success_url(self):
        if self._parent:
            return reverse('product_api',
                           kwargs={'pk': self._parent.id})
        else:
            return reverse('product-list')


##############################
# Treatment
class TreatmentApi(APIView):
    authentication_classes = []
    permission_classes = []
    http_method_names = ['get']

    def get(self, request, *args, **kwargs):
        itemId = kwargs['pk']
        template_name = 'catalogue/catalogue_model_show.html'
        item = get_object_or_404(Treatment, pk=itemId)
        product = item.batch.product_variant.product
        subtitle = 'treatment'
        values = [{'name': 'name', 'value': item.name},
                  {'name': 'batch', 'value': item.batch},
                  {'name': 'rate & unit',
                   'value': '{} {}'.format(item.rate, item.rate_unit)}]
        thesiss = TreatmentThesis.objects.filter(treatment=item)
        extraData = {}
        foundTrials = 0
        foundThesis = 0
        for thesist in thesiss:
            thesis = thesist.thesis
            trial = thesis.field_trial
            nameTrial = trial.name
            if nameTrial not in extraData:
                extraData[nameTrial] = {'id': trial.id,
                                        'thesis': []}
                foundTrials += 1
            foundThesis += 1
            extraData[nameTrial]['thesis'].append(
                {'id': thesis.id, 'name': thesis.getTitle()})
        foundRelations = [{'name': name,
                           'id': extraData[name]['id'],
                           'thesis': extraData[name]['thesis']}
                          for name in extraData]

        return render(request, template_name,
                      {'product': product,
                       'values': values,
                       'item': item,
                       'foundTrials': foundTrials,
                       'foundThesis': foundThesis,
                       'foundRelations': foundRelations,
                       'subtitle': subtitle,
                       'update_url': subtitle + '-update',
                       'delete_url': subtitle + '-delete'})


class TreatmentFormLayout(FormHelper):
    def __init__(self, new=True):
        super().__init__()
        title = 'New Treatment' if new else 'Update Treatment'
        submitTxt = 'Create' if new else 'Save'
        self.add_layout(Layout(Div(
            HTML(title), css_class="h4 mt-4"),
            Div(
                Field('name', css_class='mb-3'),
                Field('rate', css_class='mb-3'),
                Field('rate_unit', css_class='mb-3'),
                FormActions(
                    Submit('submit', submitTxt, css_class="btn btn-info"),
                    css_class='text-sm-end'),
                css_class="card-body-baas mt-2")
        ))


class TreatmentForm(forms.ModelForm):
    class Meta:
        model = Treatment
        fields = ['name', 'rate', 'rate_unit']

    def __init__(self, *args, **kwargs):
        super(TreatmentForm, self).__init__(*args, **kwargs)
        self.fields['name'].required = False
        self.fields['rate'].label = 'Dosis'
        self.fields['rate_unit'].label = 'Dosis Unit'


class TreatmentCreateView(LoginRequiredMixin, CreateView):
    model = Treatment
    form_class = TreatmentForm
    template_name = 'baaswebapp/model_edit_form.html'

    def form_valid(self, form):
        if form.is_valid():
            item = form.instance
            item.batch_id = self.kwargs["reference_id"]
            item.save()
            batch = Batch.objects.get(id=item.batch_id)
            return HttpResponseRedirect(
                batch.get_absolute_url())

    def get_form(self, form_class=TreatmentForm):
        form = super().get_form(form_class)
        form.helper = TreatmentFormLayout()
        return form


class TreatmentUpdateView(LoginRequiredMixin, UpdateView):
    model = Treatment
    form_class = TreatmentForm
    template_name = 'baaswebapp/model_edit_form.html'

    def get_form(self, form_class=TreatmentForm):
        form = super().get_form(form_class)
        form.helper = TreatmentFormLayout(new=False)
        return form


class TreatmentDeleteView(DeleteView):
    model = Treatment
    template_name = 'catalogue/treatment_delete.html'
    _parent = None

    def delete(self, request, *args, **kwargs):
        self.object = self.get_object()
        self._parent = self.object.batch
        self.object.delete()
        return HttpResponseRedirect(self.get_success_url())

    def get_success_url(self):
        if self._parent:
            return reverse('batch-api',
                           kwargs={'pk': self._parent.id})
        else:
            return reverse('product-list')
