from django.urls import path

from .user import views as user_views
from .facilitator import views as facilitator_views
from .location import views as location_views
from .school import views as school_views
from .workshop import views as workshop_views

app_name = "registration"
urlpatterns = [
    path("workshop/", workshop_views.workshop, name="workshop"),
    path("workshop/<int:id>/", workshop_views.workshop_id, name="workshop_id"),
    path("workshops/bulk/", workshop_views.workshops_bulk, name="workshops_bulk"),
    path("locations/bulk/", location_views.locations_bulk, name="locations_bulk"),
    path("location/", location_views.location, name="location"),
    path("location/<int:id>/", location_views.location_id, name="location_id"),
    path("facilitator/", facilitator_views.facilitator, name="facilitator"),
    path("facilitator/login/", facilitator_views.login_facilitator, name="login"),
    path(
        "facilitator/set-up/",
        facilitator_views.facilitator_account_set_up,
        name="facilitator_set_up",
    ),
    path(
        "facilitator/register/",
        facilitator_views.register_facilitator,
        name="register_facilitator",
    ),
    path("user/", user_views.user),
    path("users/", user_views.users),
    path("login/", user_views.login_user),
    path("logout/", user_views.logout_user),
    path("schools/", school_views.schools),
    path("schools/bulk/", school_views.schools_bulk, name="schools_bulk"),
    path("users/request-reset-password/", user_views.request_password_reset),
    path("users/reset-password/", user_views.reset_password),
]
