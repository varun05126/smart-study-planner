from django.contrib import admin
from .models import Subject, Task

@admin.register(Subject)
class SubjectAdmin(admin.ModelAdmin):
    list_display = ("name",)


@admin.register(Task)
class TaskAdmin(admin.ModelAdmin):
    list_display = ("title", "subject", "deadline", "estimated_hours", "completed")
    list_filter = ("subject", "completed")
    search_fields = ("title",)