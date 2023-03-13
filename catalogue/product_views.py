# Create your views here.
from django_filters.views import FilterView
from django.contrib.auth.mixins import LoginRequiredMixin
from catalogue.models import Product, Batch, Treatment, ProductVariant
from trialapp.models import Crop, Plague, AssessmentType
from trialapp.data_models import ThesisData, DataModel, ReplicaData
from django.shortcuts import render, get_object_or_404
from rest_framework.views import APIView
from baaswebapp.graphs import Graph
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
                css_class="card-body-baas mt-2")
            ))


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
    FILTER_DATA = [TAG_DIMENSIONS, TAG_CROPS, TAG_PLAGUES, TAG_LEVEL]

    def identifyObjectFilter(self, tags):
        dimensions = []
        crops = []
        plagues = []
        level = Graph.L_REPLICA
        for tag in tags:
            tagTypes = tag.split('-')
            tagType = tagTypes[0]
            if tagType in ProductApi.FILTER_DATA:
                tagId = tagTypes[1]
                if tagType == ProductApi.TAG_CROPS:
                    crops.append(Crop.objects.get(pk=tagId))
                if tagType == ProductApi.TAG_DIMENSIONS:
                    dimensions.append(AssessmentType.objects.get(pk=tagId))
                if tagType == ProductApi.TAG_PLAGUES:
                    plagues.append(Plague.objects.get(pk=tagId))
                if tagType == ProductApi.TAG_LEVEL:
                    if tagId == Graph.L_THESIS:
                        level = Graph.L_THESIS
                    elif tagId == Graph.L_REPLICA:
                        level = Graph.L_REPLICA
        return dimensions, crops, plagues, level

    def calcularGraphs(self, product, tags, graphPerRow=2):
        if 'show_data' not in tags:
            return [], '', 'col-md-12'
        dimensions, crops, plagues, level = self.identifyObjectFilter(tags)
        classGroup = Graph.classColGraphs(len(crops), graphPerRow)
        if len(dimensions) == 0:
            return [], 'Please select dimensions', classGroup
        if len(crops) == 0:
            return [], 'Please select crop', classGroup

        croplagues = []
        for crop in crops:
            if len(plagues) > 0:
                for plague in plagues:
                    croplagues.append([crop, plague])
            else:
                croplagues.append([crop, None])

        graphs = []
        for dimension in dimensions:
            graphDim = self.fetchData(product, dimension,
                                      croplagues, graphPerRow,
                                      level)
            graphs.append(graphDim)
        return graphs, '', classGroup

    def fetchData(self, product, dimension, croplagues,
                  graphPerRow, level):
        graphDim = {'name': "{}".format(dimension.name),
                    'values': []}
        lastRow = []

        for croplague in croplagues:
            # Get graph
            crop = croplague[0]
            plague = croplague[1]
            nameItem = crop.name
            if plague:
                nameItem += '-' + plague.name
            graph = self.computeGraph(product, crop, plague, dimension, level)

            item = {'name': nameItem, 'graph': graph}
            lastRow.append(item)
            if len(lastRow) % graphPerRow == 0:
                graphDim['values'].append(lastRow)
                lastRow = []

        if len(lastRow) > 0:
            graphDim['values'].append(lastRow)

        return graphDim

    def computeGraph(self, product, crop, plague,
                     assessmentType, level):
        dataClass = None
        # Fetch Data
        if level == Graph.L_THESIS:
            dataClass = ThesisData
        elif level == Graph.L_REPLICA:
            dataClass = ReplicaData

        dataPointsT, trialAssessmentSets = dataClass.getDataPointsProduct(
            product, crop, plague, assessmentType)

        if dataPointsT:
            graphT = Graph(level, trialAssessmentSets, dataPointsT,
                           xAxis=Graph.L_DATE, combineTrialAssessments=True)
            if level == Graph.L_THESIS:
                graphPlotsT, classGraphT = graphT.scatter()
            elif level == Graph.L_REPLICA:
                graphPlotsT, classGraphT = graphT.violin()
            return graphPlotsT[0][0]
        else:
            return 'No data found'

    def get(self, request, *args, **kwargs):
        product_id = None
        product_id = kwargs['product_id']
        template_name = 'catalogue/product_show.html'
        product = get_object_or_404(Product, pk=product_id)

        filterData = [
            {'name': ProductApi.TAG_CROPS,
             'values': DataModel.getCrops(product)},
            {'name': ProductApi.TAG_PLAGUES,
             'values': DataModel.getPlagues(product)},
            {'name': ProductApi.TAG_DIMENSIONS,
             'values': DataModel.dimensionsValues(product)}]
        graphs, errorgraphs, classGraphCol = self.calcularGraphs(product,
                                                                 request.GET)
        return render(request, template_name,
                      {'product': product,
                       'deleteProductForm': ProductDeleteView(),
                       'fieldtrials': DataModel.getCountFieldTrials(product),
                       'filterData': filterData,
                       'graphs': graphs,
                       'batches': Batch.getItems(product),
                       'variants': ProductVariant.getItems(product),
                       'treatments': Treatment.displayItems(product),
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


class BatchFormHelper(FormHelper):
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
        fields = ['name', 'serial_number', 'rate', 'rate_unit',
                  'product_variant']

    def __init__(self, *args, **kwargs):
        product_id = kwargs.pop('product_id')
        new = kwargs.pop('new')
        super(BatchForm, self).__init__(*args, **kwargs)
        self.fields['product_variant'].queryset =\
            ProductVariant.objects.filter(product_id=product_id).order_by(
                'name')
        self.helper = BatchFormHelper(new=new)
        self.fields['serial_number'].required = False


class BatchCreateView(LoginRequiredMixin, CreateView):
    form_class = BatchForm
    template_name = 'baaswebapp/model_edit_form.html'
    model = Batch

    def get_form_kwargs(self):
        kwargs = super(BatchCreateView, self).get_form_kwargs()
        kwargs.update({'product_id': self.kwargs.get('product_id')})
        kwargs.update({'new': True})
        return kwargs

    def form_valid(self, form):
        if form.is_valid():
            item = form.instance
            item.product_id = self.kwargs["product_id"]
            item.save()
            product = Product.objects.get(id=item.product_id)
            return HttpResponseRedirect(product.get_absolute_url())


class BatchUpdateView(LoginRequiredMixin, UpdateView):
    model = Batch
    form_class = BatchForm
    template_name = 'baaswebapp/model_edit_form.html'

    def get_form_kwargs(self):
        kwargs = super(BatchUpdateView, self).get_form_kwargs()
        batch = Batch.objects.get(id=self.kwargs.get('pk'))
        product = batch.product_variant.product
        kwargs.update({'product_id': product.id})
        kwargs.update({'new': False})
        return kwargs


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


class ProductVariantFormHelper(FormHelper):
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
        new = kwargs.pop('new')
        super(ProductVariantForm, self).__init__(*args, **kwargs)
        self.helper = ProductVariantFormHelper(new=new)
        self.fields['description'].required = False


class ProductVariantCreateView(LoginRequiredMixin, CreateView):
    model = ProductVariant
    form_class = ProductVariantForm
    template_name = 'baaswebapp/model_edit_form.html'

    def get_form_kwargs(self):
        kwargs = super(ProductVariantCreateView, self).get_form_kwargs()
        kwargs.update({'new': True})
        return kwargs

    def form_valid(self, form):
        if form.is_valid():
            item = form.instance
            item.product_id = self.kwargs["product_id"]
            item.save()
            Batch.createDefault(item)
            return HttpResponseRedirect(item.product.get_absolute_url())


class ProductVariantUpdateView(LoginRequiredMixin, UpdateView):
    model = ProductVariant
    form_class = ProductVariantForm
    template_name = 'baaswebapp/model_edit_form.html'

    def get_form_kwargs(self):
        kwargs = super(ProductVariantUpdateView, self).get_form_kwargs()
        kwargs.update({'new': False})
        return kwargs


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
        return render(request, template_name,
                      {'product': product,
                       'values': values,
                       'item': item,
                       'subtitle': subtitle,
                       'update_url': subtitle + '-update',
                       'delete_url': subtitle + '-delete'})


class TreatmentFormHelper(FormHelper):
    def __init__(self, new=True):
        super().__init__()
        title = 'New Treatment' if new else 'Update Treatment'
        submitTxt = 'Create' if new else 'Save'
        self.add_layout(Layout(Div(
            HTML(title), css_class="h4 mt-4"),
            Div(
                Field('name', css_class='mb-3'),
                Field('batch', css_class='mb-3'),
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
        fields = ['name', 'batch', 'rate', 'rate_unit']

    def __init__(self, *args, **kwargs):
        product_id = kwargs.pop('product_id')
        new = kwargs.pop('new')
        super(TreatmentForm, self).__init__(*args, **kwargs)
        self.fields['batch'].queryset =\
            Batch.objects.filter(
                product_variant__product_id=product_id).order_by(
                    'name')
        self.fields['name'].required = False
        self.helper = TreatmentFormHelper(new=new)
        self.fields['rate'].label = 'Dosis'
        self.fields['rate_unit'].label = 'Dosis Unit'


class TreatmentCreateView(LoginRequiredMixin, CreateView):
    model = Treatment
    form_class = TreatmentForm
    template_name = 'baaswebapp/model_edit_form.html'

    def get_form_kwargs(self):
        kwargs = super(TreatmentCreateView, self).get_form_kwargs()
        product_id = self.kwargs.get('product_id')
        kwargs.update({'product_id': product_id})
        kwargs.update({'new': True})
        return kwargs

    def form_valid(self, form):
        if form.is_valid():
            item = form.instance
            item.product_id = self.kwargs["product_id"]
            item.save()
            product = Product.objects.get(id=item.product_id)
            return HttpResponseRedirect(product.get_absolute_url())


class TreatmentUpdateView(LoginRequiredMixin, UpdateView):
    model = Treatment
    form_class = TreatmentForm
    template_name = 'baaswebapp/model_edit_form.html'

    def get_form_kwargs(self):
        kwargs = super(TreatmentUpdateView, self).get_form_kwargs()
        treatment = Treatment.objects.get(id=self.kwargs.get('pk'))
        product = treatment.batch.product_variant.product
        kwargs.update({'product_id': product.id})
        kwargs.update({'new': False})
        return kwargs


class TreatmentDeleteView(DeleteView):
    model = Treatment
    template_name = 'catalogue/treatment_delete.html'

    def delete(self, *args, **kwargs):
        self.object = self.get_object()
        product_id = self.object.batch.product_variant.product_id
        self.object.delete()
        product = Product.objects.get(id=product_id)
        return HttpResponseRedirect(product.get_absolute_url())
