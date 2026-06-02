"""
URL configuration for backend project.

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
from django.urls import path, include, re_path
from .views import render_home, serve_react
from .auth_views import login_view

urlpatterns = [
    path('admin/', admin.site.urls),
    path('api/auth/login/', login_view, name='login'),
    path('api/tours/', include('tours.urls')),
    path('api/agents/', include('agents.urls')),
    #catch all url, must be at bottom of paths
    re_path(r'^.*$', serve_react, name="serve_react"),
]
