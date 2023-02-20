# Create your views here.
from django_filters.views import FilterView
from django.contrib.auth.mixins import LoginRequiredMixin
from catalogue.models import Product  # , Batch, Treatment, ProductVariant
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


class ProductForm(FormHelper):
    def __init__(self, new=True):
        super().__init__()
        title = 'New product' if new else 'Upate product'
        submitTxt = 'Create' if new else 'Save'
        self.add_layout(Layout(Div(
            HTML(title), css_class="h4 mt-4"),
            Div(Field('name', css_class='mb-3'),
                Field('vendor', css_class='mb-3'),
                Field('category', css_class='mb-3'),
                FormActions(
                    Submit('submit', submitTxt, css_class="btn btn-info"),
                    css_class='text-sm-end'),
                css_class="card-body-baas col-md-4 mt-2")
            ))


class ProductCreateView(LoginRequiredMixin, CreateView):
    model = Product
    fields = ['name', 'vendor', 'category']
    template_name = 'baaswebapp/model_edit_form.html'

    def get_form(self, form_class=None):
        form = super().get_form(form_class)
        form.helper = ProductForm()
        return form


class ProductUpdateView(LoginRequiredMixin, UpdateView):
    model = Product
    fields = ['name', 'vendor', 'category']
    template_name = 'baaswebapp/model_edit_form.html'

    def get_form(self, form_class=None):
        form = super().get_form(form_class)
        form.helper = ProductForm(new=False)
        return form


class ProductDeleteView(DeleteView):
    model = Product
    success_url = reverse_lazy('product-list')
    template_name = 'catalogue/product_delete.html'
    success_message = 'Your Product has been deleted successfully.'


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
    http_method_names = ['delete', 'get', 'post']
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
                       'errors': errorgraphs,
                       'classGraphCol': classGraphCol,
                       'titleView': product.getName()})


# class BatchForm(FormHelper):
#     def __init__(self, new=True):
#         super().__init__()
#         title = 'New product' if new else 'Upate product'
#         submitTxt = 'Create' if new else 'Save'
#         self.add_layout(Layout(Div(
#             HTML(title), css_class="h4 mt-4"),
#             Div(Field('product', css_class='mb-3'),
#                 Field('name', css_class='mb-3'),
#                 Field('serial_number', css_class='mb-3'),
#                 Field('rate', css_class='mb-3'),
#                 Field('rate_unit', css_class='mb-3'),
#                 FormActions(
#                     Submit('submit', submitTxt, css_class="btn btn-info"),
#                     css_class='text-sm-end'),
#                 css_class="card-body-baas col-md-4 mt-2")
#             ))


# class BatchCreateView(LoginRequiredMixin, CreateView):
#     model = Batch
#     fields = ['name', 'vendor', 'category']
#     template_name = 'baaswebapp/model_edit_form.html'

#     def get_form(self, form_class=None):
#         form = super().get_form(form_class)
#         form.helper = BatchForm()
#         return form


# class BatchUpdateView(LoginRequiredMixin, UpdateView):
#     model = Batch
#     fields = ['name', 'vendor', 'category']
#     template_name = 'baaswebapp/model_edit_form.html'

#     def get_form(self, form_class=None):
#         form = super().get_form(form_class)
#         form.helper = BatchForm(new=False)
#         return form


# class BatchDeleteView(DeleteView):
#     model = Batch
#     success_url = reverse_lazy('product-list')
