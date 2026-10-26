from django.contrib import messages
from django.contrib.admin.views.decorators import staff_member_required
from django.contrib.auth import login, logout
from django.contrib.auth.decorators import login_required
from django.db.models import Q
from django.shortcuts import get_object_or_404, redirect, render
from django.views.decorators.http import require_POST

from .forms import ClintForm, CreateUserForm, LoginForm
from .models import Clint


# Create your views here.
def index(request):
    return render(request, "web/index.html")


def register(request):
    form = CreateUserForm(request.POST or None)
    if request.method == "POST" and form.is_valid():
        form.save()
        messages.success(request, "Your account was created. You can now sign in.")
        return redirect("my_login")

    return render(request, "web/register.html", {"form": form})


# login user
def my_login(request):
    form = LoginForm(request, data=request.POST or None)
    if request.method == "POST" and form.is_valid():
        user = form.get_user()
        login(request, user)
        messages.success(request, "Login successful.")
        if user.is_staff:
            return redirect("dashboard")
        messages.info(request, "Customer records are available to staff accounts.")
        return redirect("Home")

    return render(request, "web/login.html", {"form": form})


@login_required(login_url="my_login")
@require_POST
def my_logout(request):
    logout(request)
    messages.success(request, "Logout successful.")
    return redirect("my_login")


@staff_member_required(login_url="my_login")
def dashboard(request):
    clints = Clint.objects.select_related("category").all()
    return render(
        request, "web/dashboard.html", {"clints": clints, "form": ClintForm()}
    )


@staff_member_required(login_url="my_login")
def add_clint(request):
    form = ClintForm(request.POST or None)
    if request.method == "POST" and form.is_valid():
        form.save()
        messages.success(request, "Client added successfully.")
        return redirect("dashboard")

    clints = Clint.objects.select_related("category").all()
    return render(request, "web/dashboard.html", {"clints": clints, "form": form})


@staff_member_required(login_url="my_login")
@require_POST
def delete(request, id):
    clint = get_object_or_404(Clint, id=id)
    clint.delete()
    messages.success(request, "Client deleted successfully.")
    return redirect("dashboard")


@staff_member_required(login_url="my_login")
def view(request, id):
    clint = get_object_or_404(Clint, id=id)
    return render(request, "web/view.html", {"clint": clint})


@staff_member_required(login_url="my_login")
def edit(request, id):
    clint = get_object_or_404(Clint, id=id)
    form = ClintForm(request.POST or None, instance=clint)
    if request.method == "POST" and form.is_valid():
        form.save()
        messages.success(request, "Client updated successfully.")
        return redirect("dashboard")

    return render(request, "web/edit.html", {"form": form})


@staff_member_required(login_url="my_login")
def search(request):
    query = request.GET.get("query", "").strip()
    results = Clint.objects.none()
    if query:
        results = Clint.objects.select_related("category").filter(
            Q(first_name__icontains=query) | Q(id__icontains=query)
        )

    return render(request, "web/search.html", {"results": results, "query": query})


def custom_page_not_found(request, exception):
    return render(request, "web/404.html", status=404)
