from django.urls import path

from . import views

app_name = "verifications"
urlpatterns = [
    path("request/", views.request_verification, name="request"),
    path("verify/", views.verify, name="verify"),
]
