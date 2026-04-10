import os
from slack_sdk import WebClient

import pytz
#gsheets


CANCELLATION_CHANNEL_ID = "C0AKSD2DQ06"



slack_client = WebClient(token=os.environ.get("SLACK_BOT_TOKEN"))

def slack_cancellation(time:str, guest_name:str, week_number:int, week_day: str):
    try:

        text = f"@channel (no ping for testing) {guest_name} has cancelled their tour at {time} on {week_day} (Week {week_number}). Please notify the ambassador assigned to this tour."
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