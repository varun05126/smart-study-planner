from django.urls import path
from . import views

urlpatterns = [
    path("", views.login_view, name="login"),
    path("signup/", views.signup_view, name="signup"),
    path("logout/", views.logout_view, name="logout"),

    path("dashboard/", views.dashboard, name="dashboard"),
    path("add-task/", views.add_task, name="add_task"),

    # -------- StudyStack Notes --------
    path("notes/add/", views.add_note, name="add_note"),
    path("notes/my/", views.my_notes, name="my_notes"),
    path("notes/library/", views.public_library, name="public_library"),
    path("notes/save/<int:note_id>/", views.toggle_save_note, name="toggle_save_note"),
]