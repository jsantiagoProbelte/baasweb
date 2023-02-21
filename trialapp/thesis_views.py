# Create your views here.
from django.views.generic.list import ListView
from django.contrib.auth.mixins import LoginRequiredMixin
# from rest_framework import permissions
from catalogue.models import Product  # , Batch
from trialapp.models import FieldTrial, ProductThesis, RateUnit,\
    Thesis, Replica
from django.shortcuts import get_object_or_404, render
from rest_framework.views import APIView
from rest_framework.response import Response
from trialapp.trial_helper import LayoutTrial
from django.views.generic.edit import CreateView, UpdateView, DeleteView
from crispy_forms.helper import FormHelper
from django.urls import reverse_lazy, reverse
from crispy_forms.layout import Layout, Div, Submit, Field, HTML
from crispy_forms.bootstrap import FormActions
from django.http import HttpResponseRedirect
from django import forms


class ThesisListView(LoginRequiredMixin, ListView):
    model = Thesis
    paginate_by = 100  # if pagination is desired
    login_url = '/login'

    def get_context_data(self, **kwargs):
        field_trial_id = self.kwargs['field_trial_id']
        fieldTrial = get_object_or_404(FieldTrial, pk=field_trial_id)
        new_list = Thesis.getObjects(fieldTrial)
        headerRows = LayoutTrial.headerLayout(fieldTrial)
        return {'object_list': new_list,
                'fieldTrial': fieldTrial,
                'rowsReplicaHeader': headerRows,
                'rowsReplicas': LayoutTrial.showLayout(fieldTrial,
                                                       None,
                                                       new_list)}


class ManageProductToThesis(APIView):
    authentication_classes = []
    permission_classes = []
    http_method_names = [
        'delete', 'post']

    def post(self, request, format=None):
        thesis_id = request.POST['thesis_id'].split('-')[-1]
        thesis = get_object_or_404(Thesis, pk=thesis_id)
        product_id = request.POST['product']
        product = get_object_or_404(Product, pk=product_id)
        rate = request.POST['rate']
        rate_unit_id = request.POST['rate_unit']
        rateUnit = get_object_or_404(RateUnit, pk=rate_unit_id)
        # batch_id = request.POST['batch']
        # batch = get_object_or_404(Batch, pk=batch_id)

        productThesis = ProductThesis(
            thesis=thesis,
            # batch=batch,
            product=product,
            rate_unit=rateUnit,
            rate=rate)
        productThesis.save()
        responseData = {
            'id': productThesis.id,
            'product': product.name,
            # 'batch': batch.name,
            'rate_unit': rateUnit.name,
            'rate': rate}
        return Response(responseData)

    def delete(self, request, *args, **kwargs):
        productThesis = ProductThesis.objects.get(
            pk=request.POST['item_id'])
        productThesis.delete()

        response_data = {'msg': 'Product was deleted.'}
        return Response(response_data, status=200)


class ManageReplicaToThesis(APIView):
    authentication_classes = []
    permission_classes = []
    http_method_names = [
        'delete', 'post']

    def post(self, request, format=None):
        thesis_id = request.POST['thesis_id'].split('-')[-1]
        thesis = get_object_or_404(Thesis, pk=thesis_id)
        count = Replica.objects.filter(thesis=thesis).count()
        replica = Replica.objects.create(
            thesis=thesis,
            pos_x=0,
            pos_y=0,
            number=count+1)

        responseData = {
            'id': replica.id,
            'pos_x': replica.pos_x,
            'pos_y': replica.pos_y,
            'number': replica.number}

        return Response(responseData)

    def delete(self, request, *args, **kwargs):
        replica = Replica.objects.get(
            pk=request.POST['replica_id'])
        replica.delete()

        response_data = {'msg': 'Product was deleted.'}
        return Response(response_data, status=200)


class ThesisFormLayout(FormHelper):
    def __init__(self, new=True):
        super().__init__()
        title = 'New thesis' if new else 'Edit thesis'
        submitTxt = 'Create' if new else 'Save'
        self.add_layout(Layout(Div(
            HTML(title), css_class="h4 mt-4"),
            Div(Field('name', css_class='mb-3'),
                Field('number_applications', css_class='mb-3'),
                Field('interval', css_class='mb-3'),
                Field('first_application', css_class='mb-3'),
                Field('mode', css_class='mb-3'),
                Field('description', css_class='mb-3'),
                FormActions(
                    Submit('submit', submitTxt, css_class="btn btn-info"),
                    css_class='text-sm-end'),
                css_class="card-body-baas col-md-4 mt-2")
            ))


class MyDateInput(forms.widgets.DateInput):
    def get_context(self, name, value, attrs):
        context = super().get_context(name, value, attrs)
        # use the browser's HTML date picker (no css/javascript required)
        context['widget']['type'] = 'date'
        return context


class ThesisForm(forms.ModelForm):
    class Meta:
        model = Thesis
        fields = ('name', 'number_applications', 'interval', 'mode',
                  'description', 'first_application')
        widgets = {
            'first_application': MyDateInput()
        }


class ThesisCreateView(LoginRequiredMixin, CreateView):
    model = Thesis
    form_class = ThesisForm
    template_name = 'baaswebapp/model_edit_form.html'

    def get_form(self, form_class=ThesisForm):
        form = super().get_form(form_class)
        form.helper = ThesisFormLayout()
        return form

    def form_valid(self, form):
        if form.is_valid():
            form.instance.field_trial_id = self.kwargs["field_trial_id"]
            thesis = form.instance
            thesis.number = Thesis.objects.filter(
                field_trial_id=thesis.field_trial_id).count()+1
            thesis.save()
            return HttpResponseRedirect(self.get_success_url())
        else:
            pass

    def get_success_url(self):
        return reverse(
            'thesis-list',
            kwargs={'field_trial_id': self.kwargs["field_trial_id"]})


class ThesisUpdateView(LoginRequiredMixin, UpdateView):
    model = Thesis
    form_class = ThesisForm
    template_name = 'baaswebapp/model_edit_form.html'

    def get_form(self, form_class=ThesisForm):
        form = super().get_form(form_class)
        form.helper = ThesisFormLayout(new=False)
        return form


class ThesisDeleteView(DeleteView):
    model = Thesis
    success_url = reverse_lazy('thesis-list')
    template_name = 'trialapp/thesis_delete.html'
    _field_trial_id = None

    def delete(self, *args, **kwargs):
        self.object = self.get_object()
        self._field_trial_id = self.object.field_trial_id
        self.object.delete()
        return HttpResponseRedirect(self.get_success_url())

    def get_success_url(self):
        return reverse(
            'thesis-list',
            kwargs={'field_trial_id': self._field_trial_id})


class ThesisApi(APIView):
    authentication_classes = []
    permission_classes = []
    http_method_names = ['get']

    def get(self, request, *args, **kwargs):
        template_name = 'trialapp/thesis_show.html'
        thesis_id = kwargs['thesis_id']
        thesis = get_object_or_404(Thesis, pk=thesis_id)

        return render(
            request, template_name, {
                'fieldTrial': thesis.field_trial,
                'thesis': thesis,
                'title': thesis.getTitle(),
                'product_list': ProductThesis.getObjects(thesis),
                'replica_list': Replica.getObjects(thesis),
                'products': Product.getSelectList(asDict=True),
                'rate_units': RateUnit.getSelectList(asDict=True)})
