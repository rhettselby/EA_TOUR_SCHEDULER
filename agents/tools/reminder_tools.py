from datetime import timedelta
import concurrent
from django.utils import timezone

import pytz
from tours.models import Tour

def get_history(days_back: int) -> dict:
    """
    Use this when someone asks about recent tours, this tool provides information on tours given in the 
    last 'days_back' days.
    """
    print(f"Retrieving tour history")

    try:

        pst = pytz.timezone('America/Los_Angeles')
        #Create two week zone starting at beginning of current week
        today = timezone.now().astimezone(pst)
        start_range = today - timedelta(days=days_back)
        tours = Tour.objects.filter(start_dt__gte=start_range).order_by('start_dt')

        result = []

        #must create new thread when performing sync operations inside async process (agent calls asyncio.run())
        def db_ops():
            for tour in tours:
                result.append({
                    "event_id": tour.event_id,
                    "start": tour.start_dt.astimezone(pst).strftime("%a %b %d, %I:%M %p"),
                    "number_of_guests": tour.number_of_guests,
                    "group_tour": tour.group_tour,
                    "guest_name": tour.guest_name,
                    "status": tour.status,
                })
        
        with concurrent.futures.ThreadPoolExecutor() as pool:
            pool.submit(db_ops).result()
        
        return {
            'tours': result,
            'status': "All tours from last two weeks retrieved successfully"
        }

    except Exception as e:
       return {
            "status": "Unable to retrive tours",
            "error": str(e),
            }