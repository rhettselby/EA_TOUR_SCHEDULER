from django.shortcuts import redirect, render
from .models import Tour
import pytz

from datetime import timedelta
from django.utils import timezone
import time

from tours.tasks import TourScraper
# Create your views here.


def view_tours(request):

    pst = pytz.timezone('America/Los_Angeles')

    #Create two week zone
    today = timezone.now().astimezone(pst)
    start_of_week = today - timedelta(days=today.weekday())
    end_of_week = start_of_week + timedelta(days=14)

    #Django uses PST since we are passing timezone aware datetimes to filter
    tours = Tour.objects.filter(start_dt__gte=start_of_week, end_dt__lte=end_of_week).order_by('start_dt')

    #Convert times to PST
    for tour in tours:
        tour.start_dt = tour.start_dt.astimezone(pst)
        tour.end_dt = tour.end_dt.astimezone(pst)
    
    return render(request, 'tours/view.html', {'tours': tours})


def get_tours(request):
    TourScraper.delay()
    return redirect("/tours/")


