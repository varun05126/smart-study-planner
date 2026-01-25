from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth import authenticate, login, logout
from django.contrib.auth.decorators import login_required
from django.contrib.auth.models import User
from django.utils import timezone
from django.db.models import Sum

from django.http import HttpResponse

from core.services.leetcode import get_leetcode_stats

from .models import (
    Subject, Task, TaskMessage, Note, StudyStreak, LearningGoal,
    StudySession, Topic, Platform, PlatformAccount,
    UserStats, DailyActivity, Resource
)

from .forms import (
    SignupForm, SubjectForm, TaskForm, NoteForm,
    LearningGoalForm, StudySessionForm, GitHubUsernameForm
)

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
# TASKS
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


@login_required
def task_detail(request, task_id):
    task = get_object_or_404(Task, id=task_id, user=request.user)
    messages = task.messages.all()

    if request.method == "POST":
        user_msg = request.POST.get("message")
        if user_msg:
            TaskMessage.objects.create(task=task, sender="user", content=user_msg)

            try:
                ai_reply = generate_task_ai_reply(task, user_msg)
            except Exception:
                ai_reply = "⚠️ AI error. Try again."

            TaskMessage.objects.create(task=task, sender="ai", content=ai_reply)
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

    prompt = f"""
User needs help.

Title: {task.title}
Subject: {task.custom_subject or task.subject}
Type: {task.task_type}

Ask clarifying questions, then guide solution.
"""

    try:
        ai_reply = generate_task_ai_reply(task, prompt)
    except Exception:
        ai_reply = "⚠️ AI error. Try again."

    TaskMessage.objects.create(task=task, sender="ai", content=ai_reply)
    task.ai_solution = ai_reply
    task.needs_help = False
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
    stats, _ = UserStats.objects.get_or_create(user=request.user)

    # ---------------- PLATFORM ACCOUNTS ----------------
    github = PlatformAccount.objects.filter(user=request.user, platform__slug="github").first()
    leetcode = PlatformAccount.objects.filter(user=request.user, platform__slug="leetcode").first()
    gfg = PlatformAccount.objects.filter(user=request.user, platform__slug="gfg").first()
    codeforces = PlatformAccount.objects.filter(user=request.user, platform__slug="codeforces").first()
    hackerrank = PlatformAccount.objects.filter(user=request.user, platform__slug="hackerrank").first()

    # ---------------- STATS ----------------
    github_commits = stats.total_commits or 0
    leetcode_solved = stats.leetcode_solved or 0
    leetcode_xp = stats.leetcode_xp or 0

    # (future ready)
    gfg_solved = getattr(stats, "gfg_solved", 0) if hasattr(stats, "gfg_solved") else 0
    codeforces_solved = getattr(stats, "codeforces_solved", 0) if hasattr(stats, "codeforces_solved") else 0
    hackerrank_solved = getattr(stats, "hackerrank_solved", 0) if hasattr(stats, "hackerrank_solved") else 0

    # ---------------- TOTAL XP ----------------
    total_xp = stats.total_xp or 0
    level = max(1, total_xp // 100 + 1)

    context = {
        # CORE
        "stats": stats,
        "total_xp": total_xp,
        "level": level,

        # GITHUB
        "github": github,
        "github_commits": github_commits,

        # LEETCODE
        "leetcode": leetcode,
        "leetcode_solved": leetcode_solved,
        "leetcode_xp": leetcode_xp,

        # OTHER PLATFORMS
        "gfg": gfg,
        "codeforces": codeforces,
        "hackerrank": hackerrank,

        # SOLVED COUNTS (UI)
        "gfg_solved": gfg_solved,
        "codeforces_solved": codeforces_solved,
        "hackerrank_solved": hackerrank_solved,
    }

    return render(request, "core/profile.html", context)

# ==================================================
# STUDY
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
# GITHUB USERNAME SYSTEM
# ==================================================

@login_required
def github_connect(request):
    return redirect("add_github")


@login_required
def add_github_username(request):
    platform, _ = Platform.objects.get_or_create(
        slug="github",
        defaults={"name": "GitHub", "base_url": "https://github.com"}
    )

    if request.method == "POST":
        form = GitHubUsernameForm(request.POST)
        if form.is_valid():
            PlatformAccount.objects.update_or_create(
                user=request.user,
                platform=platform,
                defaults={
                    "username": form.cleaned_data["username"],
                    "profile_url": f"https://github.com/{form.cleaned_data['username']}"
                }
            )
            return redirect("profile")   # 👈 this is why you go to profile
    else:
        form = GitHubUsernameForm()

    return render(request, "core/add_github.html", {"form": form})


@login_required
def sync_github(request):
    account = get_object_or_404(
        PlatformAccount, user=request.user, platform__slug="github"
    )
    from core.services.github_username import sync_github_by_username
    sync_github_by_username(account)
    return redirect("profile")


@login_required
def github_activity(request):
    account = PlatformAccount.objects.filter(
        user=request.user, platform__slug="github"
    ).first()

    activities = DailyActivity.objects.filter(account=account) if account else []

    return render(request, "core/github_activity.html", {
        "account": account,
        "activities": activities
    })

@login_required
def github_callback(request):
    """
    OAuth callback placeholder.
    You are currently using username-based sync, not OAuth.
    """
    return HttpResponse("GitHub OAuth is not enabled. Please add your GitHub username instead.")

@login_required
def disconnect_github(request):
    PlatformAccount.objects.filter(
        user=request.user,
        platform__slug="github"
    ).delete()
    return redirect("profile")


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


# --------------------------------------------------
# Alias to satisfy old URL name
# --------------------------------------------------

@login_required
def sync_github_username(request):
    return sync_github(request)


# ================= LEETCODE =================

@login_required
def add_leetcode(request):
    platform, _ = Platform.objects.get_or_create(
        slug="leetcode",
        defaults={"name": "LeetCode", "base_url": "https://leetcode.com"}
    )

    if request.method == "POST":
        username = request.POST.get("username")

        if username:
            PlatformAccount.objects.update_or_create(
                user=request.user,
                platform=platform,
                defaults={
                    "username": username,
                    "profile_url": f"https://leetcode.com/{username}"
                }
            )
            return redirect("leetcode_sync")

    return render(request, "core/add_leetcode.html")

@login_required
def leetcode_sync(request):
    try:
        from core.services.leetcode import sync_leetcode_by_username
        sync_leetcode_by_username(request.user)
    except Exception as e:
        print("LeetCode sync error:", e)

    return redirect("profile")

    from core.services.leetcode import get_leetcode_stats

    data = get_leetcode_stats(stats.leetcode_username)

    easy = data.get("easy", 0)
    medium = data.get("medium", 0)
    hard = data.get("hard", 0)
    total = data.get("total", 0)

    xp = easy * 5 + medium * 10 + hard * 20

    stats.leetcode_solved = total
    stats.leetcode_xp = xp

    # total system update
    stats.total_problems = total
    stats.total_xp = stats.total_commits * 10 + xp
    stats.level = max(1, stats.total_xp // 100 + 1)

    stats.save()

    return redirect("profile")


@login_required
def disconnect_leetcode(request):
    stats, _ = UserStats.objects.get_or_create(user=request.user)
    stats.leetcode_solved = 0
    stats.leetcode_xp = 0

    if hasattr(stats, "leetcode_username"):
        stats.leetcode_username = ""

    stats.save()
    return redirect("profile")

# ================= GFG =================

@login_required
def add_gfg(request):
    platform, _ = Platform.objects.get_or_create(
        slug="gfg",
        defaults={"name": "GeeksForGeeks", "base_url": "https://geeksforgeeks.org"}
    )

    if request.method == "POST":
        username = request.POST.get("username")

        if username:
            PlatformAccount.objects.update_or_create(
                user=request.user,
                platform=platform,
                defaults={
                    "username": username,
                    "profile_url": f"https://auth.geeksforgeeks.org/user/{username}/"
                }
            )
            return redirect("profile")

    return render(request, "core/add_gfg.html")


@login_required
def gfg_sync(request):
    from core.services.gfg import sync_gfg_by_username
    sync_gfg_by_username(request.user)
    return redirect("profile")


@login_required
def disconnect_gfg(request):
    PlatformAccount.objects.filter(
        user=request.user,
        platform__slug="gfg"
    ).delete()
    return redirect("profile")

# ================= CODEFORCES =================

@login_required
def add_codeforces(request):
    platform, _ = Platform.objects.get_or_create(
        slug="codeforces", defaults={"name": "Codeforces"}
    )

    if request.method == "POST":
        username = request.POST.get("username")
        PlatformAccount.objects.update_or_create(
            user=request.user,
            platform=platform,
            defaults={"username": username}
        )
        return redirect("profile")

    return render(request, "core/add_codeforces.html")


@login_required
def codeforces_sync(request):
    from core.services.codeforces import sync_codeforces_by_username
    sync_codeforces_by_username(request.user)
    return redirect("profile")


@login_required
def disconnect_codeforces(request):
    PlatformAccount.objects.filter(
        user=request.user, platform__slug="codeforces"
    ).delete()
    return redirect("profile")


# ================= HACKERRANK =================

@login_required
def add_hackerrank(request):
    platform, _ = Platform.objects.get_or_create(
        slug="hackerrank", defaults={"name": "HackerRank"}
    )

    if request.method == "POST":
        username = request.POST.get("username")
        PlatformAccount.objects.update_or_create(
            user=request.user,
            platform=platform,
            defaults={"username": username}
        )
        return redirect("profile")

    return render(request, "core/add_hackerrank.html")


@login_required
def hackerrank_sync(request):
    from core.services.hackerrank import sync_hackerrank_by_username
    sync_hackerrank_by_username(request.user)
    return redirect("profile")


@login_required
def disconnect_hackerrank(request):
    PlatformAccount.objects.filter(
        user=request.user, platform__slug="hackerrank"
    ).delete()
    return redirect("profile")