from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth import authenticate, login, logout
from django.contrib.auth.decorators import login_required
from django.contrib.auth.models import User
from django.utils import timezone
from django.db.models import Sum

from .models import (
    Subject, Task, Note, StudyStreak, LearningGoal,
    StudySession, Topic,
    Platform, PlatformAccount
)

from .forms import (
    SignupForm, SubjectForm, TaskForm, NoteForm,
    LearningGoalForm, StudySessionForm
)

from core.services.github import sync_github_activity


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
        "streak": streak,
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
            task.save()
            return redirect("dashboard")
    else:
        form = TaskForm()
        form.fields["subject"].queryset = Subject.objects.all()

    return render(request, "core/add_task.html", {"form": form})


@login_required
def toggle_task(request, task_id):
    task = get_object_or_404(Task, id=task_id, user=request.user)
    task.completed = not task.completed
    task.save()

    if task.completed:
        update_streak(request.user)

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
        "saved_notes": []
    })


@login_required
def public_library(request):
    notes = Note.objects.filter(
        visibility="public"
    ).exclude(user=request.user).order_by("-created_at")

    return render(request, "core/public_library.html", {"notes": notes})


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

    platforms = Platform.objects.filter(is_active=True)
    connected = PlatformAccount.objects.filter(user=request.user)
    connected_slugs = set(connected.values_list("platform__slug", flat=True))

    platform_status = []
    for p in platforms:
        platform_status.append({
            "name": p.name,
            "slug": p.slug,
            "connected": p.slug in connected_slugs
        })

    return render(request, "core/profile.html", {
        "goals": goals,
        "streak": streak,
        "total_minutes": total_minutes,
        "platforms": platform_status
    })


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

            update_streak(request.user)
            return redirect("dashboard")
    else:
        form = StudySessionForm()

    return render(request, "core/add_study_session.html", {"form": form})


@login_required
def study_history(request):
    sessions = StudySession.objects.filter(user=request.user).order_by("-study_date", "-id")

    total_minutes = sessions.aggregate(Sum("duration_minutes"))["duration_minutes__sum"] or 0

    return render(request, "core/study_history.html", {
        "sessions": sessions,
        "total_minutes": total_minutes
    })


# ================= PLATFORM SYNC =================

@login_required
def sync_github(request):
    account = get_object_or_404(
        PlatformAccount,
        user=request.user,
        platform__slug="github"
    )

    sync_github_activity(account)
    return redirect("profile")


# ================= STREAK ENGINE =================

def update_streak(user):
    today = timezone.now().date()
    streak, _ = StudyStreak.objects.get_or_create(user=user)

    if streak.last_active == today:
        return
    elif streak.last_active == today - timezone.timedelta(days=1):
        streak.current_streak += 1
    else:
        streak.current_streak = 1

    streak.last_active = today
    streak.longest_streak = max(streak.longest_streak, streak.current_streak)
    streak.save()