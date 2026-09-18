from django.urls import path

from . import views


app_name = "assessment"
urlpatterns = [
    path("", views.home, name="home"),
    path("dashboard/", views.dashboard, name="dashboard"),
    path("t/<uuid:public_id>/<str:token>/", views.open_invitation, name="open_invitation"),
    path("assessment/<uuid:attempt_id>/welcome/", views.welcome, name="welcome"),
    path("assessment/<uuid:attempt_id>/<int:number>/", views.question, name="question"),
    path("completed/", views.completed, name="completed"),
    path("results/<uuid:public_id>/", views.result, name="result"),
    path("results/<uuid:public_id>/delete/", views.delete_invitation, name="delete_invitation"),
    path("results/<uuid:public_id>/export/<str:format_name>/", views.export_result, name="export_result"),
]
