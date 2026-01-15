from django.shortcuts import render, redirect
from .models import Task
from .forms import TaskForm


def home(request):
    return render(request, "core/home.html")


def add_task(request):
    form = TaskForm(request.POST or None)
    if form.is_valid():
        form.save()
        return redirect("task_list")
    return render(request, "core/add_task.html", {"form": form})


def task_list(request):
    tasks = Task.objects.select_related("subject").order_by("deadline")
    return render(request, "core/task_list.html", {"tasks": tasks})

def dashboard(request):
    tasks = Task.objects.all()
    total = tasks.count()
    completed = tasks.filter(completed=True).count()
    pending = total - completed

    return render(request, "core/dashboard.html", {
        "total": total,
        "completed": completed,
        "pending": pending,
        "tasks": tasks.order_by("deadline")[:5]
    })

def edit_task(request, task_id):
    task = Task.objects.get(id=task_id)
    form = TaskForm(request.POST or None, instance=task)
    if form.is_valid():
        form.save()
        return redirect("task_list")
    return render(request, "core/edit_task.html", {"form": form})


def delete_task(request, task_id):
    task = Task.objects.get(id=task_id)
    if request.method == "POST":
        task.delete()
        return redirect("task_list")
    return render(request, "core/delete_task.html", {"task": task})

def toggle_task(request, task_id):
    task = Task.objects.get(id=task_id)
    task.completed = not task.completed
    task.save()
    return redirect("task_list")

