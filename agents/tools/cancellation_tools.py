import os
from slack_sdk import WebClient

#Re-exported so the cancellation_agent keeps importing get_channel_id from this
#module. Defining a wrapper here shadowed the import and recursed into itself,
#so every cancellation silently fell through to FALLBACK_CHANNEL_ID instead of
#using CHANNEL_MAP.
from agents.tools.slack_tools import get_channel_id, FALLBACK_CHANNEL_ID

import pytz
#gsheets


CANCELLATION_CHANNEL_ID = FALLBACK_CHANNEL_ID

slack_client = WebClient(token=os.environ.get("SLACK_BOT_TOKEN"))

def slack_cancellation(channel_id: str, time:str, guest_name:str, week_number:int, week_day: str):
    try:
        
        text = f"<!channel> {guest_name} has cancelled their tour at {time} on {week_day} (Week {week_number})."
        slack_client.chat_postMessage(
            channel = channel_id,
            text = text,
        )

        return {
            "status": "Message sent to slack channel",
            "channel_id": CANCELLATION_CHANNEL_ID,
            "message": text,
        }
    except Exception as e:
        return ({"error": f"Failed to send cancellation notification: {e}"})