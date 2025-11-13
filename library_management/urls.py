from django.urls import path
from . import views

app_name = "library_management"

urlpatterns = [
    path("", views.home, name="home"),
]
