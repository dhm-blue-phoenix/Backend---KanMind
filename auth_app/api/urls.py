# Django
from django.urls import path

# Local imports
from .views import UserRegistrationView, UserLoginView

urlpatterns = [
    path('registration/', UserRegistrationView.as_view(), name='register'),
    path('login/', UserLoginView.as_view(), name='login'),
]