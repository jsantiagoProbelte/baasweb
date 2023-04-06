from django_filters.views import FilterView
from django.contrib.auth.mixins import LoginRequiredMixin
from baaswebapp.models import RateTypeUnit
from catalogue.models import Product, Batch, Treatment, ProductVariant
from trialapp.models import Crop, Plague, TreatmentThesis
from trialapp.data_models import ThesisData, DataModel, ReplicaData, Assessment
from django.shortcuts import render, get_object_or_404
from rest_framework.views import APIView
from baaswebapp.graphs import GraphTrial
from django.views.generic.edit import CreateView, UpdateView, DeleteView
from crispy_forms.helper import FormHelper
from django.urls import reverse_lazy
from crispy_forms.layout import Layout, Div, Submit, Field, HTML
from crispy_forms.bootstrap import FormActions
from django import forms
from django.http import HttpResponseRedirect


class ProductFormLayout(FormHelper):
    def __init__(self, new=True):
        super().__init__()
        title = 'New product' if new else 'Edit product'
        submitTxt = 'Create' if new else 'Save'
        self.add_layout(Layout(Div(
            HTML(title), css_class="h4 mt-4"),
            Div(Field('name', css_class='mb-3'),
                Field('vendor', css_class='mb-3'),
                Field('category', css_class='mb-3'),
                FormActions(
                    Submit('submit', submitTxt, css_class="btn btn-info"),
                    css_class='text-sm-end'),
                css_class="card-body-baas mt-2")))


class ProductForm(forms.ModelForm):
    class Meta:
        model = Product
        fields = ('name', 'vendor', 'category')


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


class ProductListView(LoginRequiredMixin, FilterView):
    model = Product
    paginate_by = 100  # if pagination is desired
    login_url = '/login'
    template_name = 'catalogue/product_list.html'

    def get_context_data(self, **kwargs):
        new_list = []
        objectList = Product.getObjects()
        for item in objectList:
            new_list.append({
                'name': item.name,
                'fieldtrials': DataModel.getCountFieldTrials(item),
                'crops': DataModel.getCrops(item),
                'plagues': DataModel.getPlagues(item),
                'dimensions': DataModel.dimensionsValues(item),
                'id': item.id})
        return {'object_list': new_list,
                'titleList': '({}) Products'.format(len(objectList))}


class ProductApi(APIView):
    authentication_classes = []
    permission_classes = []
    http_method_names = ['get']
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
        dataClass = None
        # Fetch Data
        if level == GraphTrial.L_THESIS:
            dataClass = ThesisData
        elif level == GraphTrial.L_REPLICA:
            dataClass = ReplicaData

        dataPointsT, fieldTrials = dataClass.getDataPointsProduct(
            product, crop, plague, rateType, ratedPart)

        if dataPointsT:
            graphT = GraphTrial(level, rateType, ratedPart, dataPointsT,
                                xAxis=GraphTrial.L_DATE,
                                combineTrialAssessments=False)
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
                                 batch=batch).order_by('name'):
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

    def get(self, request, *args, **kwargs):
        product_id = None
        product_id = kwargs['product_id']
        template_name = 'catalogue/product_show.html'
        product = get_object_or_404(Product, pk=product_id)
        filterData, titleGraph = self.filterData(request.GET, product)
        graphs, errorgraphs, classGraphCol = self.calcularGraphs(product,
                                                                 request.GET)
        return render(request, template_name,
                      {'product': product,
                       'deleteProductForm': ProductDeleteView(),
                       'fieldtrials': DataModel.getCountFieldTrials(product),
                       'filterData': filterData,
                       'titleGraph': titleGraph,
                       'graphs': graphs,
                       'variants': self.getProductTree(product),
                       'errors': errorgraphs,
                       'classGraphCol': classGraphCol,
                       'titleView': product.getName()})


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
        return render(request, template_name,
                      {'product': product,
                       'values': values,
                       'item': item,
                       'subtitle': subtitle,
                       'update_url': subtitle + '-update',
                       'delete_url': subtitle + '-delete'})


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
            return HttpResponseRedirect(variant.product.get_absolute_url())


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

    def delete(self, *args, **kwargs):
        self.object = self.get_object()
        product = self.object.product_variant.product
        self.object.delete()
        return HttpResponseRedirect(product.get_absolute_url())


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
        return render(request, template_name,
                      {'product': product,
                       'item': item,
                       'values': values,
                       'subtitle': subtitle,
                       'update_url': subtitle + '-update',
                       'delete_url': subtitle + '-delete'})


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

    def delete(self, *args, **kwargs):
        self.object = self.get_object()
        product = self.object.product
        self.object.delete()
        return HttpResponseRedirect(product.get_absolute_url())


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
                batch.product_variant.get_absolute_url())

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

    def delete(self, *args, **kwargs):
        self.object = self.get_object()
        product = self.object.batch.product_variant.product
        self.object.delete()
        return HttpResponseRedirect(product.get_absolute_url())
