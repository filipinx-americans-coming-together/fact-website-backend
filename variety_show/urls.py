from django.urls import path

from . import views

app_name = 'variety_show'
urlpatterns = [
    path('tickets/', views.tickets, name='tickets'),
]