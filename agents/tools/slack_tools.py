import os
import concurrent.futures
from zoneinfo import ZoneInfo
from slack_sdk import WebClient
from tours.models import Tour

#gsheets
import gspread
from google.oauth2.service_account import Credentials
import json




slack_client = WebClient(token=os.environ.get("SLACK_BOT_TOKEN"))


CHANNEL_MAP = {
    "Monday_9": "C0AKSD2DQ06",
    "Monday_10": "C0AKSD2DQ06",
    "Monday_11": "C0AKSD2DQ06",
    "Monday_12": "C0AKSD2DQ06",
    "Monday_13": "C0AKSD2DQ06",
    "Monday_14": "C0AKSD2DQ06",
    "Monday_15": "C0AKSD2DQ06",
    #4pm
    "Monday_16": "C0B3Z8GRX28",

    "Tuesday_9": "C0AKSD2DQ06",
    "Tuesday_10": "C0AKSD2DQ06",
    "Tuesday_11": "C0AKSD2DQ06",
    "Tuesday_12": "C0AKSD2DQ06",
    "Tuesday_13": "C0AKSD2DQ06",
    "Tuesday_14": "C0AKSD2DQ06",
    "Tuesday_15": "C0AKSD2DQ06",
    #4pm
    "Tuesday_16": "C0B3Z8GRX28",

    "Wednesday_9": "C0AKSD2DQ06",
    "Wednesday_10": "C0AKSD2DQ06",
    "Wednesday_11": "C0AKSD2DQ06",
    "Wednesday_12": "C0AKSD2DQ06",
    "Wednesday_13": "C0AKSD2DQ06",
    "Wednesday_14": "C0AKSD2DQ06",
    "Wednesday_15": "C0AKSD2DQ06",
    #4pm
    "Wednesday_16": "C0B3Z8GRX28",

    "Thursday_9": "C0AKSD2DQ06",
    "Thursday_10": "C0AKSD2DQ06",
    "Thursday_11": "C0AKSD2DQ06",
    "Thursday_12": "C0AKSD2DQ06",
    "Thursday_13": "C0AKSD2DQ06",
    "Thursday_14": "C0AKSD2DQ06",
    "Thursday_15": "C0AKSD2DQ06",
    #4pm
    "Thursday_16": "C0B3Z8GRX28",

    "Friday_9": "C0AKSD2DQ06",
    "Friday_10": "C0AKSD2DQ06",
    "Friday_11": "C0AKSD2DQ06",
    "Friday_12": "C0AKSD2DQ06",
    "Friday_13": "C0AKSD2DQ06",
    "Friday_14": "C0AKSD2DQ06",
    "Friday_15": "C0AKSD2DQ06",
    #4pm
    "Friday_16": "C0B3Z8GRX28",
}

SHEET_URL = "https://docs.google.com/spreadsheets/d/1_6kLQ8NRn08nXQw9C6Cl0QIszBXUis9zmqxb-DHlt3k/edit?gid=0#gid=0"

def send_slack_message(channel_id:str, week_day: str, week_number: int, sheet_url: str, time: str, major_of_interest: str, contact_name: str, cell_number: str) -> dict:
    """
    Send message to slack channel corresponding with given information to help coordinate tour"
    """

    #debug print statements
    print(f"Attempting to send message to channel {channel_id}")
    print(f"Token exists: {bool(os.environ.get('SLACK_BOT_TOKEN'))}")

    if week_number < 1 or week_number > 10:
        return {
            "status": f"Skipped, tour during week {week_number} not in weeks 1-10"
        }
    
    #Note time should already be passed in PST string format

    try:
        text = ""
        if contact_name and cell_number and major_of_interest:
            text = (
                f"<!channel> You have an upcoming tour on {week_day} (Week {week_number}) at {time}. {contact_name} is interested in {major_of_interest} and can be reached at {cell_number} ."
                f" Please bold your name <{sheet_url}|here> if you can take it or react with a ❌ if you can not. Thanks! \n\n" 
                f"-- Rhett & Dani "
            )
        elif major_of_interest:
            text = (
                f"<!channel> You have an upcoming tour on {week_day} (Week {week_number}) at {time}. The guest is interested in {major_of_interest}."
                f" Please bold your name <{sheet_url}|here> if you can take it or react with a ❌ if you can not. Thanks! \n\n" 
                f"-- Rhett & Dani "
            )
        else:
            text = (
                f"<!channel> You have an upcoming tour on {week_day} (Week {week_number}) at {time}. Please bold "
                f"your name <{sheet_url}|here> if you can take it or react with a ❌ if you can not. Thanks! \n\n" 
                f"-- Rhett & Dani "
            )


        slack_client.chat_postMessage(
            channel = channel_id,
            text = text
        )

        return {
            "status": "Message sent to slack channel",
            "channel_id": channel_id,
            "message": text
        }

    except Exception as e:
        print("Failed to send message" + str(e))
        return {
            "status": "Failed to send message",
            "error": str(e),
        }


def get_channel_id(week_day:str, time: int) -> dict:
    """
    Given a day of the week(monday - friday) and a time (9am - 4pm)
    return the slack channel id corresponding to that day/time
    """
    print(f"getting channel _id")

    try:
        key = week_day + "_" + str(time)
        channel_id = CHANNEL_MAP[key]
        return {
            "channel_id": channel_id,
            "status": "retrieved channel id",
        }
    
    except Exception as e:
       return {
           "channel_id": "C0AKSD2DQ06",
            "status": "Unable to retrive channel id",
            }
    
def update_tour_status(event_id: str, status: str) -> dict:
    """
    Update the tour status for a given tour in the django model database
    """
    print(f"updating tour status {event_id}")
    try:
        # Django ORM raises SynchronousOnlyOperation when called from within
        # an async context (e.g. asyncio.run inside a Celery task). Running in
        # a ThreadPoolExecutor gives us a plain thread with no event loop, so
        # Django's check passes cleanly.
        def _db_ops():
            tour = Tour.objects.get(event_id=event_id)
            old_status = tour.status
            tour.status = status
            tour.save(update_fields=['status'])
            return old_status

        with concurrent.futures.ThreadPoolExecutor() as pool:
            old_status = pool.submit(_db_ops).result()

        return {
            "status": "updated tour status",
            "old_status": old_status,
            "new_status": status,
        }

    except Tour.DoesNotExist:
        print(f"Tour {event_id} not found.")
        return {
            "status": f"Tour with event_id {event_id} not found"
        }
    except Exception as e:
        print(f"failed to update tour status: {e}")
        return {
            "status": "Failed to update tour status",
            "error": str(e)
        }


def get_sheet_url(week_number: int) -> dict:
    """
    given a week number, extract the corresponding url for that week's google sheet page
    """

    print("Getting sheet url")

    try:

        scopes = [
            "https://www.googleapis.com/auth/spreadsheets"
        ]

        creds_json = os.environ.get("GSHEETS_CREDENTIALS_JSON")
        creds_dict = json.loads(creds_json)
        creds = Credentials.from_service_account_info(creds_dict, scopes=scopes)
        gspread_client = gspread.authorize(creds)


        base_url = "https://docs.google.com/spreadsheets/d/1_rOWH5jgSI15TUSmzJ4MMtnqHqG5wdu1_K7AcjYT9MM/edit?gid=0#gid=0"
        # get worksheet gid by name
        sheet = gspread_client.open_by_key("1WE4y8-a7Zxb3dEuRp2hQ4O22JYqn9IJwFnB7Xq1ptes")
        worksheet = sheet.worksheet(f"Week {week_number}")
        gid = worksheet.id
        sheet_url = f"{base_url}#gid={gid}"

        return {
            "sheet_url" : sheet_url,
            "status": f"obtained google sheet url for week {week_number}"
        }
    
    except Exception as e:

        return {
            "sheet_url": base_url,
            "status": "Failed to obtain google sheet url",
            "error": str(e),
        }
    

def reply_to_slack_message(channel_id: str, text: str) -> dict:
    """
    Reply to a message in a slack channel with the given text
    """
    try:
        slack_client.chat_postMessage(
            channel=channel_id,
            text=text
        )
        return {"status": "Message sent", "channel_id": channel_id}
    except Exception as e:
        return {"status": "Failed", "error": str(e)}