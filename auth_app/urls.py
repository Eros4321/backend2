from django.urls import path
from .views import GoogleAuthURLView, GoogleCallbackView

urlpatterns = [
    path("google", GoogleAuthURLView.as_view(), name="google_auth"),
    path("google/callback", GoogleCallbackView.as_view(), name="google_callback"),
]
