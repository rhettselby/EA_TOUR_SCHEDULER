from django.urls import path
from . import views

app_name = 'tours'

urlpatterns = [
    path('', views.tours_api),
    path('get_tours/', views.get_tours, name = "get_tours"),
    path('<int:tour_id>/update_status/', views.update_status, name = "update_status"),
    path('scrape/', views.get_tours_api, name="get_tours_api"),
]



