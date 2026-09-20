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


#Where messages go when CHANNEL_MAP has no entry for a day/time. Update this at
#the start of each quarter along with CHANNEL_MAP - it is still the Summer 2026
#general tours channel.
FALLBACK_CHANNEL_ID = os.environ.get("SLACK_FALLBACK_CHANNEL_ID", "C0AKSD2DQ06")


CHANNEL_MAP = {
    "Monday_9": "C0C251KG00L",
    "Monday_10": "C0C1V4XQWEP",
    "Monday_11": "C0C2VNDNR08",
    "Monday_12": "C0C219QQR2N",
    "Monday_13": "C0C2VNQLQ56",
    "Monday_14": "C0C1ZDZT58W",
    "Monday_15": "C0C1L1J3HBR",
    "Monday_16": "C0C1WLSRBS9",

    "Tuesday_9": "C0C1V64TPM1",
    "Tuesday_10": "C0C2534D85S",
    "Tuesday_11": "C0C1ZET5746",
    "Tuesday_12": "C0C1V6LV8AF",
    "Tuesday_13": "C0C1L2G95EK",
    "Tuesday_14": "C0C1V6TRP7D",
    "Tuesday_15": "C0C21BDD674",
    "Tuesday_16": "C0C2VQAA2Q0",

    "Wednesday_9": "C0C1ZFH9FTQ",
    "Wednesday_10": "C0C1WN0JQUV",
    "Wednesday_11": "C0C2VQP0MLY",
    "Wednesday_12": "C0C1L3D2CDD",
    "Wednesday_13": "C0C2VQXUJEL",
    "Wednesday_14": "C0C21CAL67L",
    "Wednesday_15": "C0C1ZGATCBG",
    "Wednesday_16": "C0C1V8600BV",

    "Thursday_9": "C0C233ZC17Y",
    "Thursday_10": "C0C1YR79EHZ",
    "Thursday_11": "C0C2ZD1KW72",
    "Thursday_12": "C0C1YREUSMR",
    "Thursday_13": "C0C28NC5PAQ",
    "Thursday_14": "C0C1YRKKJV9",
    "Thursday_15": "C0C250NPFFC",
    "Thursday_16": "C0C270Y69NV",

    "Friday_9": "C0C28NN4C6Q",
    "Friday_10": "C0C20AJK6DB",
    "Friday_11": "C0C28NXCNJ0",
    "Friday_12": "C0C1PMWUV8X",
    "Friday_13": "C0C271GGEQZ",
    "Friday_14": "C0C1PN5SAJ3",
    "Friday_15": "C0C1YSGLZA7",
    "Friday_16": "C0C251K4TGS",
}


def send_slack_message(channel_id:str, week_day: str, week_number: int, date: str, sheet_url: str, time: str, major_of_interest: str, contact_name: str, cell_number: str) -> dict:
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
                f"<!channel> You have an upcoming tour on {week_day} ({date}) at {time}. {contact_name} is interested in {major_of_interest} and can be reached at {cell_number} ."
                f" Please bold your name <{sheet_url}|here> if you can take it or react with a ❌ if you can not. Thanks! \n\n" 
                f"-- Rhett & Dani "
            )
        elif major_of_interest:
            text = (
                f"<!channel> You have an upcoming tour on {week_day} ({date}) at {time}. The guest is interested in {major_of_interest}."
                f" Please bold your name <{sheet_url}|here> if you can take it or react with a ❌ if you can not. Thanks! \n\n" 
                f"-- Rhett & Dani "
            )
        else:
            text = (
                f"<!channel> You have an upcoming tour on {week_day} ({date}) at {time}. Please bold "
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
           "channel_id": FALLBACK_CHANNEL_ID,
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



SHEET_URL = f"https://docs.google.com/spreadsheets/d/{os.environ.get('GOOGLE_SHEET_ID', '')}/edit"


def get_sheet_url(week_number: int) -> dict:
    """
    Given a week number, extract the corresponding url for that week's google sheet page
    """
    print("Getting sheet url")
    base_url = SHEET_URL
    try:
        scopes = ["https://www.googleapis.com/auth/spreadsheets"]
        creds_json = os.environ.get("GSHEETS_CREDENTIALS_JSON")
        creds_dict = json.loads(creds_json)
        creds = Credentials.from_service_account_info(creds_dict, scopes=scopes)
        gspread_client = gspread.authorize(creds)

        # get worksheet gid by name
        sheet = gspread_client.open_by_key(os.environ.get("GOOGLE_SHEET_ID"))
        worksheet = sheet.worksheet(f"Week {week_number}")
        sheet_url = f"{base_url}#gid={worksheet.id}"

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