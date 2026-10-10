from django.urls import path
from . import views

app_name = "traffic"

urlpatterns = [
    path("", views.home, name="home"),
    path("dashboard/", views.dashboard, name="dashboard"),
    # path("analyze/", views.image_upload, name="image_upload"),
    path("analyze/bulk/", views.bulk_upload, name="bulk_upload"),
    path("analyze/<int:pk>/", views.image_result, name="image_result"),
    path("analytics/", views.analytics, name="analytics"),
]