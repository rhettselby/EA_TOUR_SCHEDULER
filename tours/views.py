from django.shortcuts import redirect, render
from .models import Tour
import pytz

from datetime import timedelta
from django.utils import timezone
import time

from tours.tasks import TourScraper
# Create your views here.

from rest_framework.decorators import api_view
from rest_framework.response import Response
from .serializers import TourSerializer

from rest_framework.decorators import api_view, authentication_classes, permission_classes
from rest_framework.permissions import AllowAny

from django.core.cache import cache  # django cache framwork


def view_tours(request):

    pst = pytz.timezone('America/Los_Angeles')

    #Create two week zone starting at beginning of current week
    today = timezone.now().astimezone(pst)
    start_of_week = (today - timedelta(days=today.weekday())).replace(hour=0, minute=0, second=0, microsecond=0)
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


#####View_tours returning JSON for React to render#####
@api_view(['GET'])
def tours_api(request):

    pst = pytz.timezone('America/Los_Angeles')

    #Create two week zone starting at beginning of current week
    today = timezone.now().astimezone(pst)
    start_of_week = today.replace(hour=0, minute=0, second=0, microsecond=0) - timedelta(days=today.weekday())
    end_of_week = start_of_week + timedelta(days=21)

    #Django uses PST since we are passing timezone aware datetimes to filter
    tours = Tour.objects.filter(start_dt__gte=start_of_week, end_dt__lte=end_of_week).order_by('start_dt')

    #Convert times to PST
    for tour in tours:
        tour.start_dt = tour.start_dt.astimezone(pst)
        tour.end_dt = tour.end_dt.astimezone(pst)
        #set past tour status
        if tour.start_dt < timezone.now().astimezone(pst):
            if tour.status != "past_event":
                tour.status = "past_event"
                tour.save(update_fields=['status'])

    serializer = TourSerializer(tours, many=True)

    return Response(serializer.data)




@api_view(['PATCH'])
@authentication_classes([])
@permission_classes([AllowAny])
def update_status(request, tour_id):
    tour = Tour.objects.get(id=tour_id)
    tour.status = request.data.get('status')
    tour.save()
    return Response({"message": "Tour Status Updated"})





@api_view(['POST'])
def get_tours_api(request):

    TourScraper.delay()

    return Response({"message": "OASA Tour Website Scraped"})

