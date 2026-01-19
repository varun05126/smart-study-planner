from django import forms
from django.contrib.auth.models import User
from .models import Task, Subject, Note, LearningGoal


# ================= AUTH =================

class SignupForm(forms.Form):
    username = forms.CharField(max_length=150)
    email = forms.EmailField()
    password = forms.CharField(widget=forms.PasswordInput)


# ================= SUBJECT =================

class SubjectForm(forms.ModelForm):
    class Meta:
        model = Subject
        fields = ["name"]
        widgets = {
            "name": forms.TextInput(attrs={
                "class": "form-control",
                "placeholder": "e.g. Data Structures"
            })
        }


# ================= NOTES =================

class NoteForm(forms.ModelForm):
    class Meta:
        model = Note
        fields = ["title", "subject", "text_content", "file", "visibility"]
        widgets = {
            "title": forms.TextInput(attrs={
                "class": "form-control",
                "placeholder": "Note title"
            }),
            "subject": forms.Select(attrs={
                "class": "form-control"
            }),
            "text_content": forms.Textarea(attrs={
                "rows": 5,
                "class": "form-control",
                "placeholder": "Write your notes here..."
            }),
            "visibility": forms.Select(attrs={
                "class": "form-control"
            })
        }


# ================= TASK =================

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
            "subject": forms.Select(attrs={
                "class": "form-control"
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
            "notes": forms.Textarea(attrs={
                "class": "form-control",
                "rows": 4,
                "placeholder": "Optional notes or task description..."
            }),
        }


# ================= LEARNING GOALS =================

class LearningGoalForm(forms.ModelForm):
    class Meta:
        model = LearningGoal
        fields = ["title"]
        widgets = {
            "title": forms.TextInput(attrs={
                "class": "form-control",
                "placeholder": "What do you want to learn today?"
            })
        }