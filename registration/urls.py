from django.urls import path

from .user import views as user_views
from .facilitator import views as facilitator_views
from .location import views as location_views
from .school import views as school_views
from .workshop import views as workshop_views

app_name = 'registration'
urlpatterns = [
    path('workshop/', workshop_views.workshop, name='workshop'),
    path('workshop/<int:id>/', workshop_views.workshop_id, name='workshop_id'),
    path('workshops/registrations/<int:id>/', workshop_views.workshop_registration, name='workshop_registration'),
    path('location/', location_views.location, name='location'),
    path('location/<int:id>/', location_views.location_id, name='location_id'),
    path('facilitator/', facilitator_views.facilitator, name='facilitator'),
    path('user/', user_views.user),
    path('users/', user_views.users),
    path('login/', user_views.login_user),
    path('logout/', user_views.logout_user),
    path('schools/', school_views.schools)
]