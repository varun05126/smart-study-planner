from django.shortcuts import render, redirect
from django.contrib.auth import authenticate, login, logout
from django.contrib.auth.decorators import login_required
from django.contrib.auth.models import User

from .models import Subject, Task
from .forms import SignupForm, SubjectForm, TaskForm


# ---------- AUTH ----------

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

    return render(request, "signup.html", {"form": form})


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
            error = "Invalid username or password"

    return render(request, "login.html", {"error": error})


def logout_view(request):
    logout(request)
    return redirect("login")


# ---------- DASHBOARD ----------

@login_required
def dashboard(request):
    tasks = Task.objects.filter(user=request.user)
    completed = tasks.filter(completed=True)
    pending = tasks.filter(completed=False)

    context = {
        "tasks": tasks.order_by("deadline"),
        "total_tasks": tasks.count(),
        "completed_count": completed.count(),
        "pending_count": pending.count(),
    }

    return render(request, "core/dashboard.html", context)


# ---------- SUBJECT ----------

@login_required
def add_subject(request):
    if request.method == "POST":
        form = SubjectForm(request.POST)
        if form.is_valid():
            sub = form.save(commit=False)
            sub.user = request.user
            sub.save()
            return redirect("dashboard")
    else:
        form = SubjectForm()

    return render(request, "core/add_subject.html", {"form": form})


# ---------- TASK ----------

@login_required
def add_task(request):
    if request.method == "POST":
        form = TaskForm(request.POST)
        form.fields["subject"].queryset = Subject.objects.filter(user=request.user)

        if form.is_valid():
            task = form.save(commit=False)
            task.user = request.user
            task.save()
            return redirect("dashboard")
    else:
        form = TaskForm()
        form.fields["subject"].queryset = Subject.objects.filter(user=request.user)

    return render(request, "core/add_task.html", {"form": form})
