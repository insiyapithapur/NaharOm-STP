# urls.py
from django.urls import path
from .views import ApiStatusView

urlpatterns = [
    path("status/", ApiStatusView.as_view(), name="api_status_view"),
]
