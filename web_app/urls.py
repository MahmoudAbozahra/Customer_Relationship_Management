from django.urls import path

from . import views

urlpatterns = [
    path("Home/", views.index, name="Home"),
    path("register/", views.register, name="register"),
    path("my_login/", views.my_login, name="my_login"),
    path("dashboard/", views.dashboard, name="dashboard"),
    path("my_logout/", views.my_logout, name="my_logout"),
    path("add_clint/", views.add_clint, name="add_clint"),
    path("delete/<int:id>/", views.delete, name="delete"),
    path("view/<int:id>/", views.view, name="view"),
    path("edit/<int:id>/", views.edit, name="edit"),
    path("search/", views.search, name="search"),
]
