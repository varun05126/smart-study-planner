from django.urls import path
from . import views

urlpatterns = [
    path("", views.home, name="home"),
    path("add-task/", views.add_task, name="add_task"),
    path("tasks/", views.task_list, name="task_list"),
    path("dashboard/", views.dashboard, name="dashboard"),
    path("edit/<int:task_id>/", views.edit_task, name="edit_task"),
    path("delete/<int:task_id>/", views.delete_task, name="delete_task"),
    path("toggle/<int:task_id>/", views.toggle_task, name="toggle_task"),

]
