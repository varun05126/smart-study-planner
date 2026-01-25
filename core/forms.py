from django import forms
from django.contrib.auth.models import User
from django.core.exceptions import ValidationError

from .models import (
    Subject,
    Topic,
    Task,
    Note,
    LearningGoal,
    StudySession,
    PlatformAccount,
)

# ==================================================
# AUTH
# ==================================================

class SignupForm(forms.Form):
    username = forms.CharField(
        max_length=150,
        widget=forms.TextInput(attrs={
            "placeholder": "Choose a username",
            "autocomplete": "off"
        })
    )
    email = forms.EmailField(
        widget=forms.EmailInput(attrs={
            "placeholder": "Enter your email"
        })
    )
    password = forms.CharField(
        widget=forms.PasswordInput(attrs={
            "placeholder": "Create a strong password"
        })
    )

    def clean_username(self):
        username = self.cleaned_data["username"].strip()
        if User.objects.filter(username=username).exists():
            raise ValidationError("This username is already taken.")
        return username

    def clean_email(self):
        email = self.cleaned_data["email"].strip().lower()
        if User.objects.filter(email=email).exists():
            raise ValidationError("This email is already registered.")
        return email


# ==================================================
# SUBJECT
# ==================================================

class SubjectForm(forms.ModelForm):
    class Meta:
        model = Subject
        fields = ["track", "name"]
        widgets = {
            "track": forms.Select(),
            "name": forms.TextInput(attrs={
                "placeholder": "e.g. Data Structures"
            })
        }


# ==================================================
# NOTES
# ==================================================

class NoteForm(forms.ModelForm):
    class Meta:
        model = Note
        fields = ["title", "topic", "text_content", "file", "visibility"]
        widgets = {
            "title": forms.TextInput(attrs={"placeholder": "Note title"}),
            "topic": forms.Select(),
            "text_content": forms.Textarea(attrs={
                "rows": 5,
                "placeholder": "Write your notes here..."
            }),
            "visibility": forms.Select(),
            "file": forms.ClearableFileInput(),
        }


# ==================================================
# TASK
# ==================================================

class TaskForm(forms.ModelForm):
    class Meta:
        model = Task
        fields = [
            "title",
            "subject",
            "custom_subject",
            "task_type",
            "material",
            "deadline",
            "estimated_hours",
        ]

        widgets = {
            "title": forms.TextInput(attrs={
                "placeholder": "e.g. DSA Assignment – Arrays"
            }),
            "subject": forms.Select(),
            "custom_subject": forms.TextInput(attrs={
                "placeholder": "Or enter subject manually"
            }),
            "task_type": forms.Select(),
            "material": forms.ClearableFileInput(),
            "deadline": forms.DateInput(attrs={"type": "date"}),
            "estimated_hours": forms.NumberInput(attrs={
                "step": "0.5",
                "placeholder": "e.g. 2.5"
            }),
        }

    def clean(self):
        cleaned = super().clean()
        subject = cleaned.get("subject")
        custom = cleaned.get("custom_subject")

        if not subject and not custom:
            raise ValidationError("Please select a subject or enter one manually.")

        return cleaned


# ==================================================
# LEARNING GOALS
# ==================================================

class LearningGoalForm(forms.ModelForm):
    class Meta:
        model = LearningGoal
        fields = ["title", "status"]
        widgets = {
            "title": forms.TextInput(attrs={
                "placeholder": "What do you want to learn?"
            }),
            "status": forms.Select()
        }


# ==================================================
# STUDY SESSION
# ==================================================

class StudySessionForm(forms.ModelForm):
    class Meta:
        model = StudySession
        fields = ["topic", "duration_minutes"]
        widgets = {
            "topic": forms.Select(),
            "duration_minutes": forms.NumberInput(attrs={
                "placeholder": "Time in minutes (e.g. 45)"
            }),
        }

    def clean_duration_minutes(self):
        minutes = self.cleaned_data["duration_minutes"]
        if minutes <= 0:
            raise ValidationError("Study time must be greater than zero.")
        return minutes


# ==================================================
# PLATFORM ACCOUNT (GENERIC USERNAME LINK)
# ==================================================

class PlatformAccountForm(forms.ModelForm):
    class Meta:
        model = PlatformAccount
        fields = ["username"]
        widgets = {
            "username": forms.TextInput(attrs={
                "placeholder": "Enter your platform username (e.g. octocat)"
            })
        }


# ==================================================
# GITHUB USERNAME (PUBLIC API SYNC)
# ==================================================

class GitHubUsernameForm(forms.Form):
    username = forms.CharField(
        max_length=150,
        widget=forms.TextInput(attrs={
            "placeholder": "Enter your GitHub username",
            "class": "form-control"
        })
    )

    def clean_username(self):
        username = self.cleaned_data["username"].strip()
        if " " in username:
            raise ValidationError("GitHub username cannot contain spaces.")
        return username
    