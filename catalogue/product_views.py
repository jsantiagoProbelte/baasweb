from django.contrib.auth.mixins import LoginRequiredMixin
from django.views import View
from baaswebapp.models import ModelHelpers
from django.db.models import Min, Max
from catalogue.models import Product, Batch, Treatment, ProductVariant, \
    Vendor
from trialapp.models import Crop, Plague, Product_Plague, TreatmentThesis, FieldTrial
from trialapp.filter_helpers import DetailedTrialListView
from django.shortcuts import render, get_object_or_404
from rest_framework.views import APIView
from django.views.generic.edit import CreateView, UpdateView, DeleteView
from django.utils.translation import gettext_lazy as _
from crispy_forms.helper import FormHelper
from django.urls import reverse_lazy
from crispy_forms.layout import Layout, Div, Submit, Field, HTML
from crispy_forms.bootstrap import FormActions
from django import forms
from django.http import HttpResponseRedirect
from django.urls import reverse
from baaswebapp.models import EventBaas, EventLog


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
                Field('img_link', css_class='mb-3'),
                Field('description', css_class='mb-3'),
                Field('mixes', css_class='mb-3'),
                Field('weather_temperature', css_class='mb-3'),
                Field('weather_humidity', css_class='mb-3'),
                Field('security_period', css_class='mb-3'),
                Field('presentation', css_class='mb-3'),
                Field('pest_disease', css_class='mb-3'),
                Field('concentration', css_class='mb-3'),
                Field('plagues', css_class='mb-3'),
                FormActions(
                    Submit('submit', submitTxt, css_class="btn btn-info"),
                    css_class='text-sm-end'),
                css_class="card-body-baas mt-2")))


class ProductForm(forms.ModelForm):
    notRequiredFields = ('img_link', 'description',
                         'mixes', 'weather_temperature', 'weather_humidity',
                         'security_period', 'presentation', 'pest_disease',
                         'concentration', 'active_substance', 'plagues')

    plagues = forms.ModelMultipleChoiceField(
                    queryset=Plague.objects.all().order_by("scientific"),
                    widget=forms.widgets.CheckboxSelectMultiple)

    class Meta:
        model = Product
        fields = ('name', 'vendor', 'active_substance',
                  'type_product', 'biological', 'img_link', 'description',
                  'mixes', 'weather_temperature', 'weather_humidity',
                  'security_period', 'presentation', 'pest_disease',
                  'concentration', 'active_substance')

    def __manage_plagues__(self, product):
        plagueList = self.cleaned_data.get('plagues', [])
        previousPlagueList = Product_Plague.Selectors.getPlaguesByProduct(product.id)
        addedPlagues = set(plagueList) - set(previousPlagueList)
        removedPlagues = set(previousPlagueList) - set(plagueList)

        removedProductPlagues = Product_Plague.Selectors.getPlagueProductByPlagues(removedPlagues)
        removedProductPlagues = removedProductPlagues.filter(product_id=product.id)

        for removedProductPlague in removedProductPlagues:
            removedProductPlague.delete()

        for addedPlague in addedPlagues:
            Product_Plague(product=product, plague=addedPlague).save()

    def save(self, commit=True):
        product = super().save(commit)
        if product:
            self.__manage_plagues__(product)

        return product

    def set_not_required_fields(self):
        for field in self.notRequiredFields:
            self.fields[field].required = False

    def get_options_for_target(self):
        targets = Plague.objects.all().order_by('scientific')
        return map(lambda target: (target.id, target.scientific), targets)

    def __init__(self, *args, **kwargs):
        super(ProductForm, self).__init__(*args, **kwargs)
        self.set_not_required_fields()
        vendors = Vendor.objects.all().order_by('name')

        self.fields['vendor'].queryset = vendors
        self.fields['description'].widget = forms.Textarea(
                        attrs={'rows': 5})

        product = kwargs.get('instance')
        if product:
            self.fields['plagues'].initial = Product_Plague.Selectors.getPlaguesByProduct(product.id)


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
            form.save()
            EventLog.track(EventBaas.NEW_PRODUCT,
                           self.request.user.id,
                           item.id)
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

    def form_valid(self, form):
        super().form_valid(form)
        EventLog.track(EventBaas.UPDATE_PRODUCT,
                       self.request.user.id,
                       form.instance.id)
        return HttpResponseRedirect(self.get_success_url())


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

    def getProductTree(self, product):
        data = []
        for variant in ProductVariant.getItems(product):
            variantItem = {'name': variant.name, 'id': variant.id}
            data.append(variantItem)
        return data

    def get_crop_table_data(self, id):
        crops = Crop.objects.filter(fieldtrial__product_id=id).values(
            "id", "name", "fieldtrial__name", "fieldtrial__id",
            "fieldtrial__plague__name", "fieldtrial__samples_per_replica",
            "fieldtrial__location", "fieldtrial__code")
        cropsTable = {}

        for crop in crops:
            cropName = crop["name"]
            titleTrial = FieldTrial.buildTitle(
                crop["fieldtrial__code"],
                cropName,
                crop["fieldtrial__plague__name"],
                crop["fieldtrial__location"])
            if cropName not in cropsTable:
                cropsTable[cropName] = {"trials": [], "trialsCount": 0,
                                        "name": crop["name"],
                                        "id": crop["id"], "agents": set(),
                                        "strAgents": "", "samples": 0}

            cropsTable[cropName]["trials"].append(
                {"name": titleTrial,
                    "id": crop["fieldtrial__id"]})
            cropsTable[cropName]["trialsCount"] += 1

            plagueName = None
            if 'fieldtrial__plague__name' in crop and\
               crop['fieldtrial__plague__name']:
                plagueName = crop['fieldtrial__plague__name']

            if plagueName and not ModelHelpers.isInUnknowns(plagueName):
                cropsTable[cropName]["agents"].add(plagueName)
                cropsTable[cropName]["strAgents"] = ', '.join(
                    cropsTable[cropName]["agents"])

            cropsTable[cropName]["samples"] += crop[
                "fieldtrial__samples_per_replica"]

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

    def editPermision(self, request):
        return True if request.user.is_superuser else False

    def get(self, request, *args, **kwargs):
        product_id = None
        product_id = kwargs['pk']
        template_name = 'catalogue/product_show.html'
        product = get_object_or_404(Product, pk=product_id)

        helperView = DetailedTrialListView(
            request, extra_params={'product': product_id})
        context_trials = helperView.getTrials()
        return render(
            request, template_name, {
                **context_trials,
                'product': product,
                'plagues': Product_Plague.Selectors.getPlagueNamesByProduct(product_id),
                'edit_trial_perm': self.editPermision(request),
                'range_efficacy': self.getRangeEfficacy(product),
                'variants': self.getProductTree(product),
                'titleView': product.getName(),
                'crops': self.get_crop_table_data(product_id),
                'category': product.getCategory(product.type_product).label,
                'activeTab': request.GET.get('activeTab', "1")})


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
            EventLog.track(
                EventBaas.NEW_BATCH,
                self.request.user.id,
                item.product_variant.product.id)
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

    def form_valid(self, form):
        super().form_valid(form)
        EventLog.track(EventBaas.UPDATE_BATCH,
                       self.request.user.id,
                       form.instance.product_variant.product.id)
        return HttpResponseRedirect(self.get_success_url())


class BatchDeleteView(DeleteView):
    model = Batch
    template_name = 'catalogue/batch_delete.html'
    _parent = None

    def delete(self, request, *args, **kwargs):
        self.object = self.get_object()
        self._parent = self.object.product_variant
        self.object.delete()
        EventLog.track(EventBaas.DELETE_BATCH,
                       self.request.user.id,
                       self._parent.product.id)
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
            EventLog.track(
                EventBaas.NEW_VARIANT,
                self.request.user.id,
                form.instance.product.id)
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

    def form_valid(self, form):
        super().form_valid(form)
        EventLog.track(EventBaas.UPDATE_VARIANT,
                       self.request.user.id,
                       form.instance.product.id)
        return HttpResponseRedirect(self.get_success_url())


class ProductVariantDeleteView(DeleteView):
    model = ProductVariant
    template_name = 'catalogue/product_variant_delete.html'
    _parent = None

    def delete(self, request, *args, **kwargs):
        self.object = self.get_object()
        self._parent = self.object.product
        self.object.delete()
        EventLog.track(EventBaas.DELETE_VARIANT,
                       self.request.user.id,
                       self._parent.id)
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
            EventLog.track(
                EventBaas.NEW_TREATMENT,
                self.request.user.id,
                batch.product_variant.product.id)
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

    def form_valid(self, form):
        super().form_valid(form)
        EventLog.track(EventBaas.UPDATE_TREATMENT,
                       self.request.user.id,
                       form.instance.batch.product_variant.product.id)
        return HttpResponseRedirect(self.get_success_url())


class TreatmentDeleteView(DeleteView):
    model = Treatment
    template_name = 'catalogue/treatment_delete.html'
    _parent = None

    def delete(self, request, *args, **kwargs):
        self.object = self.get_object()
        self._parent = self.object.batch
        self.object.delete()
        EventLog.track(EventBaas.DELETE_TREATMENT,
                       self.request.user.id,
                       self._parent.product_variant.product.id)
        return HttpResponseRedirect(self.get_success_url())

    def get_success_url(self):
        if self._parent:
            return reverse('batch-api',
                           kwargs={'pk': self._parent.id})
        else:
            return reverse('product-list')
