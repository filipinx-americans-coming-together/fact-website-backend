import json
from registration.models import (
    Delegate,
    Facilitator,
    FacilitatorAssistant,
    FacilitatorRegistration,
    FacilitatorWorkshop,
    Registration,
    Workshop,
)
from django.contrib.auth.models import User
from django.core import serializers


def serialize_workshop(workshop, include_fas=False):
    workshop_data = serializers.serialize(
        "json", Workshop.objects.filter(pk=workshop.pk)
    )
    location_data = serializers.serialize("json", [workshop.location])
    registrations = Registration.objects.filter(workshop_id=workshop.pk)
    facilitator_registrations = FacilitatorRegistration.objects.filter(
        workshop_id=workshop.pk
    )

    data = {
        "workshop": json.JSONDecoder().decode(workshop_data),
        "location": json.JSONDecoder().decode(location_data),
        "registrations": len(registrations) + len(facilitator_registrations),
    }

    if include_fas:
        fa_data = serializers.serialize(
            "json", FacilitatorAssistant.objects.filter(workshop_id=workshop.pk)
        )

        data["facilitator_assistants"] = json.JSONDecoder().decode(fa_data)

    return json.dumps(data)


def serialize_user(user):
    delegate_data = serializers.serialize(
        "json", Delegate.objects.filter(pk=user.delegate.pk)
    )
    user_data = serializers.serialize("json", User.objects.filter(pk=user.pk))
    registration_data = serializers.serialize(
        "json", Registration.objects.filter(delegate=user.delegate)
    )

    data = {
        "delegate": json.JSONDecoder().decode(delegate_data),
        "user": json.JSONDecoder().decode(user_data),
        "registration": json.JSONDecoder().decode(registration_data),
    }

    return json.dumps(data)


def serialize_facilitator(facilitator):
    facilitator_data = serializers.serialize("json", [facilitator])
    user_data = serializers.serialize(
        "json", User.objects.filter(pk=facilitator.user.pk)
    )
    workshops = serializers.serialize(
        "json", FacilitatorWorkshop.objects.filter(facilitator=facilitator)
    )

    registrations = FacilitatorRegistration.objects.none()

    for name in facilitator.facilitators.split(","):
        registrations = registrations | FacilitatorRegistration.objects.filter(
            facilitator_name=name.strip()
        )

    registrations = serializers.serialize("json", registrations)

    # get a list of workshops that the facilitator is facilitating
    data = {
        "facilitator": json.loads(facilitator_data),
        "user": json.loads(user_data),
        "registrations": json.loads(registrations),
        "workshops": json.loads(workshops),
    }

    return json.dumps(data)
