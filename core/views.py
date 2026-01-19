from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth import authenticate, login, logout
from django.contrib.auth.decorators import login_required
from django.contrib.auth.models import User

from .models import Subject, Task, Note
from .forms import SignupForm, SubjectForm, TaskForm, NoteForm


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

    context = {
        "tasks": tasks,
        "total_tasks": tasks.count(),
        "completed_count": tasks.filter(completed=True).count(),
        "pending_count": tasks.filter(completed=False).count(),
    }

    return render(request, "core/dashboard.html", context)


# ================= TASK =================

@login_required
def add_task(request):
    if request.method == "POST":
        form = TaskForm(request.POST, request.FILES)

        if form.is_valid():
            task = form.save(commit=False)
            task.user = request.user

            # Handle new subject
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


# ================= STUDYSTACK NOTES =================

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
    my_notes = Note.objects.filter(user=request.user)
    saved_notes = request.user.saved_notes.all()

    return render(request, "core/my_notes.html", {
        "my_notes": my_notes,
        "saved_notes": saved_notes
    })


@login_required
def public_library(request):
    notes = Note.objects.filter(visibility="public").exclude(user=request.user)
    return render(request, "core/public_library.html", {"notes": notes})


@login_required
def toggle_save_note(request, note_id):
    note = get_object_or_404(Note, id=note_id)

    if request.user in note.saved_by.all():
        note.saved_by.remove(request.user)
    else:
        note.saved_by.add(request.user)

    return redirect(request.META.get("HTTP_REFERER", "public_library"))
    