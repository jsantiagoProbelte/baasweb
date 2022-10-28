# Create your views here.
from django.views.generic.list import ListView
# from django.contrib.auth.mixins import LoginRequiredMixin
from trialapp.models import FieldTrial,  ProductApplication,\
    ProductThesis, Application
from django.shortcuts import get_object_or_404, render, redirect
from .forms import ApplicationEditForm
from rest_framework.views import APIView
from rest_framework.response import Response

# class FieldTrialListView(LoginRequiredMixin, ListView):
#    login_url = '/login'


class ApplicationListView(ListView):
    model = Application
    paginate_by = 100  # if pagination is desired

    def get_context_data(self, **kwargs):
        field_trial_id = self.kwargs['field_trial_id']
        fieldTrial = get_object_or_404(FieldTrial, pk=field_trial_id)
        new_list = Application.getObjects(fieldTrial)
        return {'object_list': new_list,
                'field_trial_name': fieldTrial.name,
                'field_trial_id': fieldTrial.id}


def editApplication(request, field_trial_id=None, application_id=None,
                    errors=None):
    initialValues = {'field_trial_id': field_trial_id,
                     'application_id': application_id}
    template_name = 'trialapp/application_edit.html'
    title = 'New'
    fieldTrial = get_object_or_404(FieldTrial, pk=field_trial_id)
    product_list = []

    if application_id is not None:
        title = 'Edit'
        application = get_object_or_404(Application, pk=application_id)

        if fieldTrial.id != application.field_trial.id:
            return redirect('fieldtrial-list', error='Bad forming Application')

        initialValues['name'] = application.name
        initialValues['application_date'] = application.application_date
        initialValues['crop_stage_majority'] = application.crop_stage_majority
        initialValues['crop_stage_scale'] = application.crop_stage_scale
        # retrieve the list of the current defined product application
        product_list = ProductApplication.getObjects(application)

    edit_form = ApplicationEditForm(initial=initialValues)
    product_list_show = [{'id': item.id, 'name': item.getName()}
                         for item in product_list]

    return render(request, template_name,
                  {'edit_form': edit_form,
                   'field_trial_id': field_trial_id,
                   'field_trial_name': fieldTrial.name,
                   'application_id': application_id,
                   'title': title,
                   'product_list': product_list_show,
                   'products': ProductThesis.getSelectListFieldTrial(
                        fieldTrial, asDict=True),
                   'errors': errors})


def saveApplication(request, application_id=None):
    values = {}
    fieldTrial = get_object_or_404(
        FieldTrial, pk=request.POST['field_trial_id'])
    if 'application_id' in request.POST and request.POST['application_id']:
        # This is not a new user review.
        application = get_object_or_404(
            Application, pk=request.POST['application_id'])
        application.field_trial = fieldTrial
        application.name = Application.getValueFromRequestOrArray(
            request, values, 'name')
        application.application_date = Application.getValueFromRequestOrArray(
            request, values, 'application_date')
        application.crop_stage_majority =\
            Application.getValueFromRequestOrArray(
                request, values, 'crop_stage_majority')
        application.crop_stage_scale = Application.getValueFromRequestOrArray(
            request, values, 'crop_stage_scale')
        application.save()
    else:
        # This is a new application
        application = Application.objects.create(
            name=Application.getValueFromRequestOrArray(
                request, values, 'name'),
            field_trial=fieldTrial,
            application_date=Application.getValueFromRequestOrArray(
                request, values, 'application_date'),
            crop_stage_majority=Application.getValueFromRequestOrArray(
                request, values, 'crop_stage_majority'),
            crop_stage_scale=Application.getValueFromRequestOrArray(
                request, values, 'crop_stage_scale')
        )

        # Create by default a list based on all the existing thesis
        # and let the user remove them
        for item in ProductThesis.getObjectsPerFieldTrial(fieldTrial):
            ProductApplication.objects.create(
                product_thesis=item,
                thesis=item.thesis,
                application=application
            )

    return redirect(
        'application-edit',
        field_trial_id=fieldTrial.id,
        application_id=application.id)


class ManageProductToApplication(APIView):
    authentication_classes = []
    permission_classes = []
    http_method_names = [
        'delete', 'post']

    def post(self, request, format=None):
        application_id = request.POST['application_id'].split('-')[-1]
        application = get_object_or_404(Application, pk=application_id)
        product_id = request.POST['product']
        productThesis = get_object_or_404(ProductThesis, pk=product_id)

        productApplication = ProductApplication(
            application=application,
            product_thesis=productThesis,
            thesis=productThesis.thesis)
        productApplication.save()
        responseData = {
            'id': productApplication.id,
            'name': productThesis.getName()}
        return Response(responseData)

    def delete(self, request, *args, **kwargs):
        productApplication = ProductApplication.objects.get(
            pk=request.POST['product_application_id'])
        productApplication.delete()

        response_data = {'msg': 'Product was deleted.'}
        return Response(response_data, status=200)
