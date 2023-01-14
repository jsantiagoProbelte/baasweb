# Create your views here.
from django_filters.views import FilterView
from django.contrib.auth.mixins import LoginRequiredMixin
from trialapp.models import Product
from django.shortcuts import render, get_object_or_404
from rest_framework.views import APIView
from rest_framework.response import Response


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
    http_method_names = ['delete', 'get']

    def delete(self, request, *args, **kwargs):
        item = Product.objects.get(
            pk=request.POST['item_id'])
        item.delete()
        response_data = {'msg': 'Product was deleted.'}
        return Response(response_data, status=200)

    def get(self, request, *args, **kwargs):
        template_name = 'catalogue/product_show.html'
        product_id = None
        if 'product_id' in request.GET:
            # for testing
            product_id = request.GET['product_id']
        elif 'product_id' in kwargs:
            # from call on server
            product_id = kwargs['product_id']
        product = get_object_or_404(Product, pk=product_id)

        return render(request, template_name,
                      {'product': product,
                       'fieldtrials': product.getCountFieldTrials(),
                       'crops': product.getCrops(),
                       'plagues': product.getPlagues(),
                       'dimensions': product.dimensionsValues(),
                       'titleView': product.getName()})
