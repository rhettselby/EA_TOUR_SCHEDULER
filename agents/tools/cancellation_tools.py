import os
from slack_sdk import WebClient

import pytz
#gsheets


CANCELLATION_CHANNEL_ID = "C0AKSD2DQ06"



slack_client = WebClient(token=os.environ.get("SLACK_BOT_TOKEN"))

def slack_cancellation(time:str, guest_name:str, week_number:int):
    try:

        text = f"@channel (no ping for testing) Cancelled Tour at {time} (week {week_number}) for {guest_name}"
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