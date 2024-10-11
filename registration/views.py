from django.shortcuts import HttpResponse, get_object_or_404
from django.http import JsonResponse
from django.core import serializers
from registration.models import Workshop, Location, Facilitator, Delegate, FacilitatorWorkshop, Registration, School
from django.contrib.auth.models import User
from django.views.decorators.csrf import csrf_exempt
from django.core.validators import validate_email
from django.contrib.auth import authenticate, login, logout


import json

def serialize_user(user):
    delegate_data = serializers.serialize('json', Delegate.objects.filter(pk=user.delegate.pk))
    user_data = serializers.serialize('json', User.objects.filter(pk=user.pk))
    registration_data = serializers.serialize('json', Registration.objects.filter(delegate=user.delegate))

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

def serialize_workshop(workshop):
    workshop_data = serializers.serialize('json', Workshop.objects.filter(pk=workshop.pk))
    location_data = serializers.serialize('json', [workshop.location])

    data = {
        'workshop': json.JSONDecoder().decode(workshop_data),
        'location': json.JSONDecoder().decode(location_data),
    }

    return json.dumps(data)


def workshop(request):
    # Note: Does not account for when attributes are missing in POST request
    if request.method == "POST":      
        try:
            data = json.loads(request.body)
            location = get_object_or_404(Location, id=data.get("location"))

            w = Workshop.objects.filter(title=data.get("title"))

            if (w.exists()):
                if (w[0].session == data.get("session")):    
                    return HttpResponse("Workshop in current session already exists")

            workshop = Workshop(
                title=data.get("title"),
                description=data.get("description"),
                facilitators=data.get("facilitators"),
                location=location,
                session=data.get("session")
            )

            workshop.save()
            return HttpResponse(status=200)
        except json.JSONDecodeError:
            return JsonResponse({"error": "Invalid JSON"}, status=400)
    elif request.method == "GET":
        data = serializers.serialize('json', Workshop.objects.all())
        return HttpResponse(data, content_type="application/json")
    else:
        return HttpResponse(status=400)

@csrf_exempt
def workshop_id(request, id):
    workshop = get_object_or_404(Workshop, location_id=id)

    if request.method == "GET":
        return HttpResponse(serialize_workshop(workshop), content_type="application/json")
    elif request.method == "PUT":       
        try:
            data = json.loads(request.body)
            location = get_object_or_404(Location, id=data.get("location"))

            workshop.title = data.get("title", workshop.title)
            workshop.description = data.get("description", workshop.description)
            workshop.facilitators = data.get("facilitators", workshop.facilitators)
            workshop.location = location
            workshop.session = data.get("session", workshop.session)

            workshop.save()
            return HttpResponse(status=200)
        except json.JSONDecodeError:
            return JsonResponse({"error": "Invalid JSON"}, status=400)
    elif request.method == "DELETE":
        workshop.delete()
        return HttpResponse(status=200)
    else:
        return HttpResponse(status=400)

@csrf_exempt
def location(request):
    if request.method == "POST":
        try:
            data = json.loads(request.body)
            obj1 = Location.objects.filter(room_num=data.get("room_num"))
            obj2 = Location.objects.filter(building=data.get("building"))
            if (obj1.exists() and obj2.exists()):
                if (obj1[0].id == obj2[0].id):
                    return HttpResponse("Location already exists")

            location = Location.objects.create(
                room_num=data.get("room_num"),
                building=data.get("building"),
                capacity=data.get("capacity")
            )
            
            location.save()

            return HttpResponse(status=200)
        except json.JSONDecodeError:
            return JsonResponse({"error": "Invalid JSON"}, status=400)
    elif request.method == "GET":
        data = serializers.serialize('json', Location.objects.all())
        return HttpResponse(data, content_type="application/json")
    else:
        return HttpResponse(status=400)

@csrf_exempt
def location_id(request, id):
    if request.method == "GET":
        data = serializers.serialize('json', Location.objects.filter(id=id))
        return HttpResponse(data, content_type="application/json")
    elif request.method == "PUT":
        try:
            data = json.loads(request.body)
            location = Location.objects.get(id=id)

            location.room_num = data.get("room_num", location.room_num)
            location.building = data.get("building", location.building)
            location.capacity = data.get("capacity", location.capacity)

            location.save()
            return HttpResponse(status=200)
        except Location.DoesNotExist:
            return JsonResponse({"error": "Location not found"}, status=404)
        except json.JSONDecodeError:
            return JsonResponse({"error": "Invalid JSON"}, status=400)
    elif request.method == "DELETE":
        Location.objects.filter(id=id).delete()
        return HttpResponse(status=200)
    else:
        return HttpResponse(status=400)
    

@csrf_exempt
def schools(request):
    """
    Handle requests related to all schools

    GET - get all schools
    """

    if request.method == 'GET':
        school_data = serializers.serialize('json', School.objects.all())

        return HttpResponse(school_data, content_type='application/json')
    else:
        return HttpResponse(status=405)
    
@csrf_exempt
def users(request):
    """
    Handle requests related to all users

    GET - get all users
    """
    
    if request.method == 'GET':
        user_data = serializers.serialize('json', User.objects.filter(is_superuser=False))

        return HttpResponse(user_data, content_type='application/json')
    else:
        return HttpResponse(status=405)

@csrf_exempt
def user(request):
    """
    Handle requests related to user

    GET - get logged in user
    PUT - update logged in user
    POST - create user
        {
            f_name: first name
            l_name: last name
            email: email (will act as username)
            password: password
            pronouns: pronouns
            year: year
            school_id: school
            workshop_1_id: id for session 1 workshop
            workshop_2_id: id for session 2 workshop
            workshop_3_id: id for session 3 workshop
        }
    DELETE - delete logged in user
    """

    user = request.user

    if request.method == 'GET':
        if (not user.is_authenticated):
            return HttpResponse('No user logged in', status=403)

        return HttpResponse(serialize_user(user), content_type='application/json')
    elif request.method == 'PUT':
        if (not user.is_authenticated):
            return HttpResponse('No user logged in', status=403)
        
        data = json.loads(request.body)

        f_name = data.get('f_name')
        l_name = data.get('l_name')
        email = data.get('email')
        password = data.get('password')
        pronouns = data.get('pronouns')
        year = data.get('year')
        school_id = data.get('school_id')

        workshop_1_id = data.get('workshop_1_id')
        workshop_2_id = data.get('workshop_2_id')
        workshop_3_id = data.get('workshop_3_id')

        workshop_ids = [workshop_1_id, workshop_2_id, workshop_3_id]

        # update data

        if f_name and len(f_name) > 0:
            user.first_name = f_name
        
        if l_name and len(l_name) > 0:
            user.last_name = l_name

        if email and len(email) > 0:
            try:
                validate_email(email)
            except:
                return HttpResponse('Invalid email', status=400)

            if (email != user.email and User.objects.filter(email=email).exists()):
                return HttpResponse('Email already in use', status=400)
            
            user.email = email
        
        if password and len(password) > 0:
            if len(password) < 0:
                return HttpResponse('Password must be at least 8 characters', status=400)
            user.set_password(password)

        if pronouns and len(pronouns) > 0:
            user.delegate.pronouns = pronouns

        if year and len(year) > 0:
            user.delegate.year = year

        if school_id:
            user.delegate.school_id = school_id

        # workshops
        sessions = []
        for workshop_id in workshop_ids:
            if workshop_id:
                session = Workshop.objects.get(pk=workshop_id).session

                if session in sessions:
                    return HttpResponse('Can not register for multiple workshops in a single session')

                sessions.append(session)
        
        print(sessions)
        print(workshop_ids)

        if len(sessions) == 3:
            # clear registered workshops
            Registration.objects.filter(delegate=user.delegate).delete()

            # re register
            for workshop_id in workshop_ids:
                workshop = Workshop.objects.get(pk=workshop_id)
                
                registration = Registration(delegate=user.delegate, workshop=workshop)

                registration.save()

        user.save()
        user.delegate.save()

        return HttpResponse(serialize_user(user), content_type='application/json')
    elif request.method == 'POST':
        data = json.loads(request.body)

        f_name = data.get('f_name')
        l_name = data.get('l_name')
        email = data.get('email')
        password = data.get('password')
        pronouns = data.get('pronouns')
        year = data.get('year')
        school_id = data.get('school_id')
        workshop_1_id = data.get('workshop_1_id')
        workshop_2_id = data.get('workshop_2_id')
        workshop_3_id = data.get('workshop_3_id')

        workshop_ids = [workshop_1_id, workshop_2_id, workshop_3_id]

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

        sessions = []
        for workshop_id in workshop_ids:
            session = Workshop.objects.get(pk=workshop_id).session

            if session in sessions:
                return HttpResponse('Can not register for multiple workshops in a single session')

            sessions.append(session)

        # set user data
        user = User(username=email, email=email, first_name=f_name, last_name=l_name)
        user.set_password(password)
        
        user.save()

        # set delegate data
        school = None

        if school_id:
            try:
                school = School.objects.get(pk=school_id)
            except:
                school = None

        delegate = Delegate(user=user, pronouns=pronouns, year=year, school=school)
        delegate.save()

        # set registration data
        for workshop_id in workshop_ids:
            workshop = Workshop.objects.get(pk=workshop_id)
            
            registration = Registration(delegate=delegate, workshop=workshop)
            registration.save()

        # login
        login(request, user)

        return HttpResponse(serialize_user(user), content_type='application/json')
    elif request.method == 'DELETE':
        if (not user.is_authenticated):
            return HttpResponse('No user logged in', status=403)
        
        data = serialize_user(user)
    
        user.delete()
        user.save()

        return HttpResponse(data, content_type='application/json')
    else: 
        return HttpResponse(status=405)
    
@csrf_exempt
def login_user(request):
    user = request.user

    if request.method == 'POST':
        data = json.loads(request.body)
        
        email = data.get('email')
        password = data.get('password')

        if email is None or len(email) == 0:
            return HttpResponse('Must provide email', status=400)
    
        if password is None or len(password) == 0:
            return HttpResponse('Must provide password', status=400)
    
        user = authenticate(username=email, password=password)

        if user is None:
            return HttpResponse('Invalid credentials', status=400)

        login(request, user)

        return HttpResponse(serialize_user(user), content_type='application/json')
    else:
        return HttpResponse(status=405)

@csrf_exempt
def logout_user(request):
    user = request.user
    if request.method == 'POST':
        if not user.is_authenticated:
            return HttpResponse('No user logged in', status=403)

        logout(request)

        return HttpResponse('Logout successful')
    else:
        return HttpResponse(status=405)
    
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

        return HttpResponse(serialize_facilitator(user.facilitator), content_type='application/json')

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

        return HttpResponse(serialize_facilitator(facilitator), content_type='application/json')

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

        return HttpResponse(serialize_facilitator(facilitator), content_type='application/json')

    elif request.method == 'DELETE':
        if not user.is_authenticated or not hasattr(user, 'facilitator'):
            return HttpResponse('No facilitator logged in', status=403)
        
        data = serialize_facilitator(user.facilitator)
    
        user.delete()

        return HttpResponse(data, content_type='application/json')

    else: 
        return HttpResponse(status=405)