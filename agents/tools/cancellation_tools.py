import os
from slack_sdk import WebClient
from tours.models import Tour

import pytz
#gsheets


CANCELLATION_CHANNEL_ID = "C0APWBP4TH8"



slack_client = WebClient(token=os.environ.get("SLACK_BOT_TOKEN"))

def slack_cancellation(event_id):
    try:
        cancelled_tour = Tour.objects.get(event_id=event_id)
        start_dt = cancelled_tour.start_dt
        pst = pytz.timezone('America/Los_Angeles')
        start_dt_pst = start_dt.astimezone(pst)
        text = f"Cancelled Tour at {start_dt_pst} ({cancelled_tour.week_number}) for {cancelled_tour.guest_name}"
        slack_client.chat_postMessage(
            channel = CANCELLATION_CHANNEL_ID,
            text = text,
        )

        return {
            "status": "Message sent to slack channel",
            "channel_id": CANCELLATION_CHANNEL_ID,
            "message": text,
        }
    except Exception as e:
        return ({"error": f"Failed to send cancellation notification: {e}"})