from django.urls import path
from . import views

app_name = "library_management"

urlpatterns = [
    path("", views.home, name="home"),
    path("dashboard/", views.admin_dashboard, name="admin_dashboard"),
    path("borrow/create/<int:book_id>/",views.create_borrow_request,name="create_borrow_request"),
    path( "borrow/history/", views.borrow_history, name="borrow_history"),
    path("borrow/cancel/<int:request_id>/",views.cancel_borrow_request,name="cancel_borrow_request"),
]
