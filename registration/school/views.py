from django.http import HttpResponse
from django.views.decorators.csrf import csrf_exempt
from django.core import serializers as django_serializers

from registration.models import School

@csrf_exempt
def schools(request):
    """
    Handle requests related to all schools

    GET - get all schools
    """

    if request.method == 'GET':
        school_data = django_serializers.serialize('json', School.objects.all())

        return HttpResponse(school_data, content_type='application/json')
    else:
        return HttpResponse(status=405)