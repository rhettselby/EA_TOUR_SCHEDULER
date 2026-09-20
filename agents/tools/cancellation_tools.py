import os
from slack_sdk import WebClient
from agents.tools.slack_tools import get_channel_id

import pytz
#gsheets


CANCELLATION_CHANNEL_ID = "C0AKSD2DQ06"




def get_channel_id(week_day:str, time: int) -> dict:
    """
    Given a day of the week(monday - friday) and a time (9am - 4pm)
    return the slack channel id corresponding to that day/time
    """
    print(f"getting channel _id")

    try:
        #call function from slack tools
        channel_id = get_channel_id(week_day, time)
        return {
            "channel_id": channel_id,
            "status": "retrieved channel id",
        }
    
    except Exception as e:
       return {
           "channel_id": "C0AKSD2DQ06",
            "status": f"Unable to retrive channel id, error : {str(e)}",
            }

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