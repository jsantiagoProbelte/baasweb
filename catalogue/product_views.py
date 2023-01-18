# Create your views here.
from django_filters.views import FilterView
from django.contrib.auth.mixins import LoginRequiredMixin
from trialapp.models import Product, Crop, Plague, AssessmentType
from trialapp.data_models import ThesisData
from django.shortcuts import render, get_object_or_404
from rest_framework.views import APIView
from rest_framework.response import Response
from baaswebapp.graphs import Graph


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
                'fieldtrials': item.getCountFieldTrials(),
                'crops': item.getCrops(),
                'plagues': item.getPlagues(),
                'dimensions': item.dimensionsValues(),
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
    FILTER_DATA = [TAG_DIMENSIONS, TAG_CROPS, TAG_PLAGUES]

    def delete(self, request, *args, **kwargs):
        item = Product.objects.get(
            pk=request.POST['item_id'])
        item.delete()
        response_data = {'msg': 'Product was deleted.'}
        return Response(response_data, status=200)

    def identifyObjectFilter(self, tags):
        dimensions = []
        crops = []
        plagues = []
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
        return dimensions, crops, plagues

    def calcularGraphs(self, product, tags, graphPerRow=3):
        if 'show_data' not in tags:
            return [], '', 'col-md-12'
        dimensions, crops, plagues = self.identifyObjectFilter(tags)
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
                                      croplagues, graphPerRow)
            graphs.append(graphDim)

        return graphs, '', classGroup

    def fetchData(self, product, dimension, croplagues, graphPerRow):
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
            graph = self.computeGraph(product, crop, plague, dimension)
            item = {'name': nameItem, 'graph': graph}
            lastRow.append(item)
            if len(lastRow) % graphPerRow == 0:
                graphDim['values'].append(lastRow)
                lastRow = []

        if len(lastRow) > 0:
            graphDim['values'].append(lastRow)

        return graphDim

    def computeGraph(self, product, crop, plague,
                     assessmentType, level=Graph.L_THESIS):
        # Thesis data
        dataPointsT, trialAssessmentSets = ThesisData.getDataPointsProduct(
            product, crop, plague, assessmentType)
        if dataPointsT:
            graphT = Graph(Graph.L_THESIS, trialAssessmentSets, dataPointsT,
                           xAxis=Graph.L_DATE, combineTrialAssessments=True)
            graphPlotsT, classGraphT = graphT.scatter()
            return graphPlotsT[0][0]
        else:
            return 'No data found'

    def get(self, request, *args, **kwargs):
        product_id = None
        if 'product_id' in request.GET:
            # for testing
            product_id = request.GET['product_id']
        elif 'product_id' in kwargs:
            # from call on server
            product_id = kwargs['product_id']
        template_name = 'catalogue/product_show.html'
        product = get_object_or_404(Product, pk=product_id)
        filterData = [
            {'name': ProductApi.TAG_CROPS, 'values': product.getCrops()},
            {'name': ProductApi.TAG_PLAGUES, 'values': product.getPlagues()},
            {'name': ProductApi.TAG_DIMENSIONS,
             'values': product.dimensionsValues()}]
        graphs, errorgraphs, classGraphCol = self.calcularGraphs(product,
                                                                 request.GET)
        return render(request, template_name,
                      {'product': product,
                       'fieldtrials': product.getCountFieldTrials(),
                       'filterData': filterData,
                       'graphs': graphs,
                       'errors': errorgraphs,
                       'classGraphCol': classGraphCol,
                       'titleView': product.getName()})
