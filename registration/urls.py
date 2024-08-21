from django.urls import path

from . import views

app_name = 'registration'
urlpatterns = [
    path('workshop/', views.workshop, name='workshop'),
    path('workshop/<int:id>/', views.workshop_id, name='workshop_id'),
    path('location/', views.location, name='location'),
    path('location/<int:id>/', views.location_id, name='location_id'),
    path('user/', views.user),
    path('users/', views.users),
    path('login/', views.login_user),
    path('logout/', views.logout_user),
    path('schools/', views.schools)
]