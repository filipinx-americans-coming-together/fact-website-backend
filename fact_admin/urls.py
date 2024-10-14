
from django.urls import path

from .login import views as login_views
from .notification import views as notification_views

app_name = 'fact_admin'
urlpatterns = [
    path('login/', login_views.login_admin, name='login_admin'),
    path('notification/', notification_views.notification, name='notification'),
    path('notifications/', notification_views.notifications, name='notifications')
]