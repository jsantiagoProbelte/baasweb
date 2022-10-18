# Create your views here.
from django.views.generic.list import ListView
# from django.contrib.auth.mixins import LoginRequiredMixin
from trialapp.models import FieldTrial

# class FieldTrialListView(LoginRequiredMixin, ListView):
#    login_url = '/login'


class FieldTrialListView(ListView):
    model = FieldTrial
    paginate_by = 100  # if pagination is desired

    def get_context_data(self, **kwargs):

        new_list = []

        # for item in FieldTrial.getObjects(self.request.user):
        for item in FieldTrial.getObjects():
            # applicationCount=5 #To use latter to display number of data
            # points and applications
            # To use latter to display number of data points and trails
            dataPoints = 33
            new_list.append({
                'name': item.name,
                'id': item.id,
                'datapoints': dataPoints})

        return {'object_list': new_list}
