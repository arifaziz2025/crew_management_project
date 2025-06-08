# File: users/urls.py (this is the correct one)

from django.urls import path
from . import views # Import the views from your current app

urlpatterns = [
    path('login/', views.login_view, name='login'),
    path('logout/', views.logout_view, name='logout'),
]