from django.urls import path
from . import views

app_name = "accounts"

urlpatterns = [
    path("signup/", views.signup_view, name="signup"),
    path("signup/done/", views.signup_done, name="signup_done"),
    path("activate/<uidb64>/<token>/", views.activate_account, name="activate"),
    path("profile/", views.profile_view, name="profile"),
    path("login/", views.login_view, name="login"),
]
