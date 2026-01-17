from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth import authenticate, login, logout
from django.contrib.auth.decorators import login_required
from django.contrib.auth.models import User

from .models import Subject, Task
from .forms import SignupForm, SubjectForm, TaskForm


# ---------- AUTH ----------

def signup_view(request):
    if request.user.is_authenticated:
        return redirect("dashboard")

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
    if request.user.is_authenticated:
        return redirect("dashboard")

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

    return render(request, "core/login.html", {"error": error})


def logout_view(request):
    logout(request)
    return redirect("login")


# ---------- DASHBOARD ----------

@login_required
def dashboard(request):
    
    tasks = Task.objects.filter(user=request.user).order_by("deadline")

    total_tasks = tasks.count()
    completed_count = tasks.filter(completed=True).count()
    pending_count = tasks.filter(completed=False).count()

    context = {
        "tasks": tasks,
        "total_tasks": total_tasks,
        "completed_count": completed_count,
        "pending_count": pending_count,
    }

    return render(request, "core/dashboard.html", context)



# ---------- SUBJECTS ----------

@login_required(login_url="login")
def subjects(request):
    subjects = Subject.objects.filter(user=request.user)

    if request.method == "POST":
        form = SubjectForm(request.POST)
        if form.is_valid():
            sub = form.save(commit=False)
            sub.user = request.user
            sub.save()
            return redirect("subjects")
    else:
        form = SubjectForm()

    return render(request, "core/subjects.html", {
        "subjects": subjects,
        "form": form
    })


@login_required(login_url="login")
def delete_subject(request, subject_id):
    subject = get_object_or_404(Subject, id=subject_id, user=request.user)
    subject.delete()
    return redirect("subjects")


# ---------- TASKS ----------

@login_required(login_url="login")
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


@login_required(login_url="login")
def mark_complete(request, task_id):
    task = get_object_or_404(Task, id=task_id, user=request.user)
    task.completed = True
    task.save()
    return redirect("dashboard")


@login_required(login_url="login")
def delete_task(request, task_id):
    task = get_object_or_404(Task, id=task_id, user=request.user)
    task.delete()
    return redirect("dashboard")
