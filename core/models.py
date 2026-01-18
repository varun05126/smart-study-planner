from django.db import models
from django.conf import settings


class Subject(models.Model):
    name = models.CharField(max_length=100)
    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE)

    def __str__(self):
        return self.name


class Task(models.Model):
    DIFFICULTY_CHOICES = [
        (1, "Very Easy"),
        (2, "Easy"),
        (3, "Medium"),
        (4, "Hard"),
        (5, "Very Hard"),
    ]

    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE)
    title = models.CharField(max_length=200)
    subject = models.ForeignKey(Subject, on_delete=models.CASCADE)
    deadline = models.DateField()
    estimated_hours = models.DecimalField(max_digits=4, decimal_places=1)
    difficulty = models.IntegerField(choices=DIFFICULTY_CHOICES)
    completed = models.BooleanField(default=False)
    notes = models.TextField(blank=True)
    uploaded_file = models.FileField(upload_to="tasks/", blank=True, null=True)
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return self.title


# ================= STUDYSTACK NOTES =================

class Note(models.Model):
    VISIBILITY_CHOICES = [
        ("private", "Private"),
        ("public", "Public"),
    ]

    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name="notes")
    title = models.CharField(max_length=200)
    subject = models.ForeignKey(Subject, on_delete=models.SET_NULL, null=True, blank=True)

    text_content = models.TextField(blank=True, null=True)
    file = models.FileField(upload_to="notes/", blank=True, null=True)

    visibility = models.CharField(max_length=10, choices=VISIBILITY_CHOICES, default="private")

    saved_by = models.ManyToManyField(settings.AUTH_USER_MODEL, related_name="saved_notes", blank=True)

    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return self.title