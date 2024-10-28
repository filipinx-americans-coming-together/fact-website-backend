import json
from registration.models import Delegate, Facilitator, FacilitatorWorkshop, Registration, Workshop
from django.contrib.auth.models import User
from django.core import serializers

def serialize_workshop(workshop):
    workshop_data = serializers.serialize('json', Workshop.objects.filter(pk=workshop.pk))
    location_data = serializers.serialize('json', [workshop.location])

    data = {
        'workshop': json.JSONDecoder().decode(workshop_data),
        'location': json.JSONDecoder().decode(location_data),
    }

    return json.dumps(data)

def serialize_user(user):
    delegate_data = serializers.serialize('json', Delegate.objects.filter(pk=user.delegate.pk))
    user_data = serializers.serialize('json', User.objects.filter(pk=user.pk))
    registration_data = serializers.serialize('json', Registration.objects.filter(user=user))

    data = {
        'delegate': json.JSONDecoder().decode(delegate_data),
        'user': json.JSONDecoder().decode(user_data),
        'registration': json.JSONDecoder().decode(registration_data)
    }

    return json.dumps(data)

def serialize_facilitator(facilitator):
    facilitator_data = serializers.serialize('json', Facilitator.objects.filter(pk=facilitator.pk))
    user_data = serializers.serialize('json', User.objects.filter(pk=facilitator.user.pk))
    facilitator_workshop_data = serializers.serialize('json', FacilitatorWorkshop.objects.filter(facilitator=facilitator))
    
    # get a list of workshops that the facilitator is facilitating
    workshop_ids = FacilitatorWorkshop.objects.filter(facilitator=facilitator).values_list('workshop_id', flat=True)
    workshop_data = serializers.serialize('json', Workshop.objects.filter(pk__in=workshop_ids))

    data = {
        'facilitator': json.loads(facilitator_data),
        'user': json.loads(user_data),
        'facilitator_workshops': json.loads(facilitator_workshop_data),
        'workshops': json.loads(workshop_data),
    }

    return json.dumps(data)