import json
from django.http import HttpResponse
from django.views.decorators.csrf import csrf_exempt
from django.core import serializers as django_serializers
from django.contrib.auth.models import User
from django.core.validators import validate_email
from django.contrib.auth import login

from registration import serializers
from registration.models import Facilitator, FacilitatorWorkshop, Workshop

@csrf_exempt
def facilitator(request):
    """
    Handle requests related to facilitator user

    GET - get logged in facilitator user
    PUT - update logged in facilitator user
    POST - create facilitator user
        {
            f_name: first name
            l_name: last name
            email: email (will act as username)
            password: password
            fa_name: fa_name
            fa_contact: fa_contact
            workshops: list of workshop ids facilitated by the user
        }
    DELETE - delete logged in facilitator user
    """

    user = request.user

    if request.method == 'GET':
        if not user.is_authenticated or not hasattr(user, 'facilitator'):
            return HttpResponse('No facilitator logged in', status=403)

        return HttpResponse(serializers.serialize_facilitator(user.facilitator), content_type='application/json')

    elif request.method == 'PUT':
        if not user.is_authenticated or not hasattr(user, 'facilitator'):
            return HttpResponse('No facilitator logged in', status=403)
        
        data = json.loads(request.body)

        f_name = data.get('f_name')
        l_name = data.get('l_name')
        email = data.get('email')
        password = data.get('password')
        fa_name = data.get('fa_name')
        fa_contact = data.get('fa_contact')
        workshops = data.get('workshops', [])

        # update user data
        if f_name and len(f_name) > 0:
            user.first_name = f_name
        
        if l_name and len(l_name) > 0:
            user.last_name = l_name

        if email and len(email) > 0:
            try:
                validate_email(email)
            except:
                return HttpResponse('Invalid email', status=400)

            if email != user.email and User.objects.filter(email=email).exists():
                return HttpResponse('Email already in use', status=400)
            
            user.email = email
        
        if password and len(password) > 0:
            if len(password) < 8:
                return HttpResponse('Password must be at least 8 characters', status=400)
            user.set_password(password)

        # update facilitator data
        facilitator = user.facilitator

        if fa_name and len(fa_name) > 0:
            facilitator.fa_name = fa_name
        
        if fa_contact and len(fa_contact) > 0:
            facilitator.fa_contact = fa_contact

        facilitator.save()

        # update facilitator workshops (different from delegate workshops)
        if workshops:
            FacilitatorWorkshop.objects.filter(facilitator=facilitator).delete()
            for workshop_id in workshops:
                workshop = Workshop.objects.get(pk=workshop_id)
                FacilitatorWorkshop.objects.create(facilitator=facilitator, workshop=workshop)

        user.save()

        return HttpResponse(serializers.serialize_facilitator(facilitator), content_type='application/json')

    elif request.method == 'POST':
        data = json.loads(request.body)

        f_name = data.get('f_name')
        l_name = data.get('l_name')
        email = data.get('email')
        password = data.get('password')
        fa_name = data.get('fa_name')
        fa_contact = data.get('fa_contact')
        workshops = data.get('workshops', [])

        # validate data
        if not f_name or len(f_name) < 1:
            return HttpResponse('First name must be at least one character', status=400)
        
        if not l_name or len(l_name) < 1:
            return HttpResponse('Last name must be at least one character', status=400)
        
        try:
            validate_email(email)
        except:
            return HttpResponse('Invalid email', status=400)
        
        if User.objects.filter(email=email).exists():
            return HttpResponse('Email already in use', status=400)
        
        if not password or len(password) < 8:
            return HttpResponse('Password must be at least 8 characters', status=400)        

        # set user data
        user = User(username=email, email=email, first_name=f_name, last_name=l_name)
        user.set_password(password)
        user.save()

        # set facilitator data
        facilitator = Facilitator(user=user, fa_name=fa_name, fa_contact=fa_contact)
        facilitator.save()

        # set facilitator workshops
        for workshop_id in workshops:
            workshop = Workshop.objects.get(pk=workshop_id)
            FacilitatorWorkshop.objects.create(facilitator=facilitator, workshop=workshop)

        # login
        login(request, user)

        return HttpResponse(serializers.serialize_facilitator(facilitator), content_type='application/json')

    elif request.method == 'DELETE':
        if not user.is_authenticated or not hasattr(user, 'facilitator'):
            return HttpResponse('No facilitator logged in', status=403)
        
        data = serializers.serialize_facilitator(user.facilitator)
    
        user.delete()

        return HttpResponse(data, content_type='application/json')

    else: 
        return HttpResponse(status=405)