from django.urls import path

from . import views


app_name = "assessment"
urlpatterns = [
    path("dashboard/", views.dashboard, name="dashboard"),
    path("t/<uuid:public_id>/<str:token>/", views.open_invitation, name="open_invitation"),
    path("assessment/<uuid:attempt_id>/<int:number>/", views.question, name="question"),
    path("completed/", views.completed, name="completed"),
]

