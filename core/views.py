from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth import authenticate, login, logout
from django.contrib.auth.decorators import login_required
from django.contrib.auth.models import User
from django.utils import timezone
from django.db.models import Sum
from django.conf import settings
from django.http import HttpResponse
import requests

from .models import (
    Subject, Task, TaskMessage, Note, StudyStreak, LearningGoal,
    StudySession, Topic, Platform, PlatformAccount,
    UserStats, DailyActivity, Resource
)

from .forms import (
    SignupForm, SubjectForm, TaskForm, NoteForm,
    LearningGoalForm, StudySessionForm
)

from core.services.github import sync_github_activity
from core.services.groq import generate_goal_solution, generate_task_ai_reply
from core.services.resources import seed_resources_by_goal


# ==================================================
# AUTH
# ==================================================

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


# ==================================================
# DASHBOARD
# ==================================================

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


# ==================================================
# TASK HUB
# ==================================================

@login_required
def tasks_hub(request):
    tasks = Task.objects.filter(user=request.user).order_by("-created_at")

    if request.method == "POST":
        form = TaskForm(request.POST, request.FILES)
        if form.is_valid():
            task = form.save(commit=False)
            task.user = request.user
            if task.task_type == "assignment" and task.material:
                task.needs_help = True
            task.save()
            return redirect("tasks_hub")
    else:
        form = TaskForm()

    total = tasks.count()
    completed = tasks.filter(completed=True).count()
    pending = total - completed
    progress = int((completed / total) * 100) if total else 0

    return render(request, "core/tasks_hub.html", {
        "form": form,
        "tasks": tasks,
        "total": total,
        "completed": completed,
        "pending": pending,
        "progress": progress
    })


@login_required
def toggle_task(request, task_id):
    task = get_object_or_404(Task, id=task_id, user=request.user)
    task.completed = not task.completed
    task.save()
    if task.completed:
        update_streak(request.user)
    return redirect("tasks_hub")


# ==================================================
# TASK DETAIL + AI CHAT
# ==================================================

@login_required
def task_detail(request, task_id):
    task = get_object_or_404(Task, id=task_id, user=request.user)
    messages = task.messages.order_by("created_at")

    if request.method == "POST":
        user_msg = request.POST.get("message")

        if user_msg:
            TaskMessage.objects.create(
                task=task,
                sender="user",
                content=user_msg
            )

            try:
                ai_reply = generate_task_ai_reply(task, user_msg)
            except Exception:
                ai_reply = "⚠️ I had trouble generating a response. Please try again."

            TaskMessage.objects.create(
                task=task,
                sender="ai",
                content=ai_reply
            )

            task.ai_solution = ai_reply
            task.needs_help = False
            task.save()

        return redirect("task_detail", task_id=task.id)

    return render(request, "core/task_detail.html", {
        "task": task,
        "messages": messages
    })


@login_required
def task_need_help(request, task_id):
    task = get_object_or_404(Task, id=task_id, user=request.user)

    intro_prompt = f"""
User needs help with this academic task.

Title: {task.title}
Subject: {task.custom_subject or task.subject}
Type: {task.task_type}

First ask 2–3 clarifying questions.
Then explain how to approach the solution.
"""

    try:
        ai_reply = generate_task_ai_reply(task, intro_prompt)
    except Exception:
        ai_reply = "⚠️ I had trouble generating a response. Please try again."

    TaskMessage.objects.create(task=task, sender="ai", content=ai_reply)

    task.needs_help = False
    task.ai_solution = ai_reply
    task.save()

    return redirect("task_detail", task_id=task.id)


# ==================================================
# NOTES
# ==================================================

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
    notes = Note.objects.filter(visibility="public").exclude(user=request.user)
    return render(request, "core/public_library.html", {"notes": notes})


# ==================================================
# LEARNING GOALS
# ==================================================

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


# ==================================================
# START LEARNING
# ==================================================

@login_required
def start_learning(request, goal_id):
    goal = get_object_or_404(LearningGoal, id=goal_id, user=request.user)

    if not goal.ai_solution:
        goal.ai_solution = generate_goal_solution(goal.title)
        goal.save()

    seed_resources_by_goal(goal.title)
    resources = Resource.objects.all().order_by("-id")[:12]

    return render(request, "core/start_learning.html", {
        "goal": goal,
        "solution": goal.ai_solution,
        "resources": resources
    })


# ==================================================
# PROFILE
# ==================================================

@login_required
def profile(request):
    goals = LearningGoal.objects.filter(user=request.user)
    streak, _ = StudyStreak.objects.get_or_create(user=request.user)

    total_minutes = StudySession.objects.filter(user=request.user)\
        .aggregate(Sum("duration_minutes"))["duration_minutes__sum"] or 0

    stats, _ = UserStats.objects.get_or_create(user=request.user)

    github_account = PlatformAccount.objects.filter(
        user=request.user,
        platform__slug="github"
    ).first()

    return render(request, "core/profile.html", {
        "goals": goals,
        "streak": streak,
        "total_minutes": total_minutes,
        "stats": stats,
        "github_account": github_account
    })


# ==================================================
# STUDY SESSION
# ==================================================

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
    sessions = StudySession.objects.filter(user=request.user).order_by("-study_date")
    total_minutes = sessions.aggregate(Sum("duration_minutes"))["duration_minutes__sum"] or 0

    return render(request, "core/study_history.html", {
        "sessions": sessions,
        "total_minutes": total_minutes
    })


# ==================================================
# GITHUB
# ==================================================

@login_required
def github_connect(request):
    client_id = settings.GITHUB_CLIENT_ID
    redirect_uri = "http://127.0.0.1:8000/platforms/github/callback/"
    scope = "read:user repo"

    url = (
        "https://github.com/login/oauth/authorize"
        f"?client_id={client_id}&redirect_uri={redirect_uri}&scope={scope}"
    )
    return redirect(url)


@login_required
def github_callback(request):
    code = request.GET.get("code")
    if not code:
        return HttpResponse("GitHub login failed", status=400)

    r = requests.post(
        "https://github.com/login/oauth/access_token",
        data={
            "client_id": settings.GITHUB_CLIENT_ID,
            "client_secret": settings.GITHUB_CLIENT_SECRET,
            "code": code,
        },
        headers={"Accept": "application/json"}
    )

    access_token = r.json().get("access_token")
    if not access_token:
        return HttpResponse("Could not get access token", status=400)

    platform = Platform.objects.get(slug="github")

    PlatformAccount.objects.update_or_create(
        user=request.user,
        platform=platform,
        defaults={"access_token": access_token, "username": request.user.username}
    )

    return redirect("profile")


@login_required
def sync_github(request):
    account = get_object_or_404(PlatformAccount, user=request.user, platform__slug="github")
    sync_github_activity(account)
    return redirect("profile")


@login_required
def github_activity(request):
    account = PlatformAccount.objects.filter(user=request.user, platform__slug="github").first()
    activities = DailyActivity.objects.filter(account=account).order_by("-date") if account else []

    return render(request, "core/github_activity.html", {
        "account": account,
        "activities": activities
    })


# ==================================================
# STREAK ENGINE
# ==================================================

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
    