from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth import authenticate, login, logout
from django.contrib.auth.decorators import login_required
from django.contrib.auth.models import User
from django.utils import timezone
from django.db.models import Sum
from django.db import models

from .models import Subject, Task, Note, StudyStreak, LearningGoal, StudySession
from .forms import (
    SignupForm, SubjectForm, TaskForm, NoteForm,
    LearningGoalForm, StudySessionForm
)

# ================= AUTH =================

def signup_view(request):
    if request.method == "POST":
        form = SignupForm(request.POST)
        if form.is_valid():
            user = User.objects.create_user(
                username=form.cleaned_data["username"],
                email=form.cleaned_data["email"],
                password=form.cleaned_data["password"]
            )
            login(request, user)
            return redirect("dashboard")
    else:
        form = SignupForm()
    return render(request, "core/signup.html", {"form": form})


def login_view(request):
    error = ""
    if request.method == "POST":
        user = authenticate(
            request,
            username=request.POST.get("username"),
            password=request.POST.get("password")
        )
        if user:
            login(request, user)
            return redirect("dashboard")
        else:
            error = "Invalid credentials"
    return render(request, "core/login.html", {"error": error})


def logout_view(request):
    logout(request)
    return redirect("login")


# ================= DASHBOARD =================

@login_required
def dashboard(request):
    tasks = Task.objects.filter(user=request.user)
    completed = tasks.filter(completed=True).count()
    total = tasks.count()
    progress = int((completed / total) * 100) if total else 0

    streak, _ = StudyStreak.objects.get_or_create(user=request.user)

    today = timezone.now().date()

    today_minutes = StudySession.objects.filter(
        user=request.user,
        study_date=today
    ).aggregate(Sum("duration_minutes"))["duration_minutes__sum"] or 0

    return render(request, "core/dashboard.html", {
        "tasks": tasks,
        "total_tasks": total,
        "completed_count": completed,
        "pending_count": tasks.filter(completed=False).count(),
        "progress": progress,
        "streak": streak.current_streak,
        "today": today,
        "today_minutes": today_minutes
    })


# ================= TASKS =================

@login_required
def add_task(request):
    if request.method == "POST":
        form = TaskForm(request.POST, request.FILES)
        if form.is_valid():
            task = form.save(commit=False)
            task.user = request.user

            new_subject = request.POST.get("new_subject")
            if new_subject:
                subject, _ = Subject.objects.get_or_create(
                    name=new_subject,
                    user=request.user
                )
                task.subject = subject

            task.save()
            return redirect("dashboard")
    else:
        form = TaskForm()
        form.fields["subject"].queryset = Subject.objects.filter(user=request.user)

    return render(request, "core/add_task.html", {"form": form})


@login_required
def toggle_task(request, task_id):
    task = get_object_or_404(Task, id=task_id, user=request.user)
    task.completed = not task.completed
    task.save()

    today = timezone.now().date()
    streak, _ = StudyStreak.objects.get_or_create(user=request.user)

    if task.completed:
        if streak.last_active == today:
            pass
        elif streak.last_active == today - timezone.timedelta(days=1):
            streak.current_streak += 1
        else:
            streak.current_streak = 1

        streak.last_active = today
        streak.longest_streak = max(streak.longest_streak, streak.current_streak)
        streak.save()

    return redirect("dashboard")


@login_required
def my_tasks(request):
    tasks = Task.objects.filter(user=request.user).order_by("deadline")
    return render(request, "core/my_tasks.html", {
        "tasks": tasks,
        "today": timezone.now().date()
    })


# ================= NOTES =================

@login_required
def add_note(request):
    if request.method == "POST":
        form = NoteForm(request.POST, request.FILES)
        if form.is_valid():
            note = form.save(commit=False)
            note.user = request.user
            note.save()
            return redirect("my_notes")
    else:
        form = NoteForm()

    return render(request, "core/add_note.html", {"form": form})


@login_required
def my_notes(request):
    return render(request, "core/my_notes.html", {
        "my_notes": Note.objects.filter(user=request.user).order_by("-created_at"),
        "saved_notes": request.user.saved_notes.all()
    })


@login_required
def public_library(request):
    notes = Note.objects.filter(
        visibility="public"
    ).exclude(user=request.user).order_by("-created_at")

    return render(request, "core/public_library.html", {"notes": notes})


@login_required
def toggle_save_note(request, note_id):
    note = get_object_or_404(Note, id=note_id)

    if request.user in note.saved_by.all():
        note.saved_by.remove(request.user)
    else:
        note.saved_by.add(request.user)

    return redirect(request.META.get("HTTP_REFERER", "public_library"))


# ================= LEARNING GOALS =================

@login_required
def learning_goals(request):
    goals = LearningGoal.objects.filter(user=request.user).order_by("-created_at")

    if request.method == "POST":
        form = LearningGoalForm(request.POST)
        if form.is_valid():
            goal = form.save(commit=False)
            goal.user = request.user
            goal.save()
            return redirect("learning_goals")
    else:
        form = LearningGoalForm()

    return render(request, "core/learning_goals.html", {
        "goals": goals,
        "form": form
    })


# ================= PROFILE =================

@login_required
def profile(request):
    goals = LearningGoal.objects.filter(user=request.user)
    streak, _ = StudyStreak.objects.get_or_create(user=request.user)

    total_minutes = StudySession.objects.filter(
        user=request.user
    ).aggregate(Sum("duration_minutes"))["duration_minutes__sum"] or 0

    return render(request, "core/profile.html", {
        "goals": goals,
        "streak": streak,
        "total_minutes": total_minutes
    })


# ================= LIVE STUDY SESSION =================

@login_required
def start_study(request):
    active = StudySession.objects.filter(user=request.user, end_time__isnull=True).first()
    if not active:
        StudySession.objects.create(user=request.user)
    return redirect("dashboard")


@login_required
def stop_study(request):
    session = StudySession.objects.filter(user=request.user, end_time__isnull=True).first()

    if session:
        session.end_time = timezone.now()
        delta = session.end_time - session.created_at
        session.duration_minutes = int(delta.total_seconds() / 60)
        session.save()

        # update streak
        today = timezone.now().date()
        streak, _ = StudyStreak.objects.get_or_create(user=request.user)

        if streak.last_active == today:
            pass
        elif streak.last_active == today - timezone.timedelta(days=1):
            streak.current_streak += 1
        else:
            streak.current_streak = 1

        streak.last_active = today
        streak.longest_streak = max(streak.longest_streak, streak.current_streak)
        streak.save()

    return redirect("dashboard")

# ================= STUDY SESSION =================

@login_required
def add_study_session(request):
    if request.method == "POST":
        form = StudySessionForm(request.POST)
        if form.is_valid():
            session = form.save(commit=False)
            session.user = request.user
            session.study_date = timezone.now().date()
            session.save()

            # ---- Update streak ----
            today = timezone.now().date()
            streak, _ = StudyStreak.objects.get_or_create(user=request.user)

            if streak.last_active == today:
                pass
            elif streak.last_active == today - timezone.timedelta(days=1):
                streak.current_streak += 1
            else:
                streak.current_streak = 1

            streak.last_active = today
            streak.longest_streak = max(streak.longest_streak, streak.current_streak)
            streak.save()

            return redirect("dashboard")
    else:
        form = StudySessionForm()
        form.fields["goal"].queryset = LearningGoal.objects.filter(user=request.user)

    return render(request, "core/add_study_session.html", {"form": form})

# ================= STUDY HISTORY =================

@login_required
def study_history(request):
    sessions = StudySession.objects.filter(user=request.user).order_by("-study_date", "-created_at")

    total_minutes = sessions.aggregate(models.Sum("duration_minutes"))["duration_minutes__sum"] or 0

    return render(request, "core/study_history.html", {
        "sessions": sessions,
        "total_minutes": total_minutes
    })