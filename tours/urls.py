from django.urls import path
from . import views

app_name = 'tours'

urlpatterns = [
    path('', views.view_tours, name = "view_tours"),
    path('get_tours', views.get_tours, name = "get_tours"),
]



