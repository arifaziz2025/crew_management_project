"""
URL configuration for cms_project project.

The `urlpatterns` list routes URLs to views. For more information please see:
    https://docs.djangoproject.com/en/5.2/topics/http/urls/
Examples:
Function views
    1. Add an import:  from my_app import views
    2. Add a URL to urlpatterns:  path('', views.home, name='home')
Class-based views
    1. Add an import:  from other_app.views import Home
    2. Add a URL to urlpatterns:  path('', Home.as_view(), name='home')
Including another URLconf
    1. Import the include() function: from django.urls import include, path
    2. Add a URL to urlpatterns:  path('blog/', include('blog.urls'))
"""
from django.contrib import admin
from django.urls import path, include
from django.conf import settings # <-- ADD THIS IMPORT
from django.conf.urls.static import static # <-- ADD THIS IMPORT

urlpatterns = [
    path('admin/', admin.site.urls),
    path('', include('crew_management.urls')), # <-- Add this line
    path('users/', include('users.urls')), # <--- ADD THIS LINE
    
]

# This is only needed when running in development mode.
# It allows Django's development server to serve uploaded media files.
if settings.DEBUG:
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)