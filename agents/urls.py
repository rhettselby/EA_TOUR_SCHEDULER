from django.urls import path
from . import views

app_name = 'agents'

urlpatterns = [
    path('slack_events/', views.slack_events, name = "slack_events")
]



