from django.urls import path

from .login import views as login_views
from .notification import views as notification_views
from .agenda import views as agenda_views
from .actions import views as action_views

app_name = "fact_admin"
urlpatterns = [
    path("login/", login_views.login_admin, name="login_admin"),
    path("", login_views.user, name="admin_user"),
    path("notification/", notification_views.notification, name="notification"),
    path(
        "notification/<int:id>/",
        notification_views.notification_id,
        name="delete-notification",
    ),
    path("notifications/", notification_views.notifications, name="notifications"),
    path("agenda-item/<int:id>/", agenda_views.agenda_items_id, name="agenda-item"),
    path("agenda-items/", agenda_views.agenda_items, name="agenda-items"),
    path(
        "agenda-items/bulk/", agenda_views.agenda_items_bulk, name="agenda-items-bulk"
    ),
    path("flags/", action_views.registration_flags, name="flags"),
    path(
        "flags/<str:label>/",
        action_views.registration_flag_id,
        name="flags-id",
    ),
    path("sheets/delegates/", action_views.delegate_sheet, name="delegate-sheet"),
    path("sheets/locations/", action_views.location_sheet, name="location-sheet"),
    path("summary/", action_views.summary, name="summary")
]
