from django import forms
from .models import Task, Subject, Note
from django.contrib.auth.models import User


class SignupForm(forms.Form):
    username = forms.CharField(max_length=150)
    email = forms.EmailField()
    password = forms.CharField(widget=forms.PasswordInput)


class SubjectForm(forms.ModelForm):
    class Meta:
        model = Subject
        fields = ["name"]


class NoteForm(forms.ModelForm):
    class Meta:
        model = Note
        fields = ["title", "subject", "text_content", "file", "visibility"]
        widgets = {
            "text_content": forms.Textarea(attrs={
                "rows": 5,
                "placeholder": "Write your notes here..."
            }),
        }


# ================= TASK FORM =================

class TaskForm(forms.ModelForm):
    class Meta:
        model = Task
        fields = [
            "title",
            "subject",
            "deadline",
            "estimated_hours",
            "difficulty",
            "notes",
            "uploaded_file",
        ]

        widgets = {
            "title": forms.TextInput(attrs={
                "class": "form-control",
                "placeholder": "e.g. Complete Unit 3 Notes"
            }),
            "deadline": forms.DateInput(attrs={
                "type": "date",
                "class": "form-control"
            }),
            "estimated_hours": forms.NumberInput(attrs={
                "class": "form-control",
                "step": "0.5",
                "placeholder": "e.g. 2.5"
            }),
            "difficulty": forms.Select(attrs={
                "class": "form-control"
            }),
            "subject": forms.Select(attrs={
                "class": "form-control"
            }),
            "notes": forms.Textarea(attrs={
                "class": "form-control",
                "rows": 4,
                "placeholder": "Optional notes or task description..."
            }),
        }
        