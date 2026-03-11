import os
from slack_sdk import WebClient
from tours.models import Tour

#gsheets
import gspread
from google.oauth2.service_account import Credentials
import json




slack_client = WebClient(token=os.environ.get("SLACK_BOT_TOKEN"))


CHANNEL_MAP = {
    "Monday_9": "C0A6EUB51U3",
    "Monday_10": "C0A65SKTA95",
    "Monday_11": "C0A70813VB3",
    "Monday_12": "C0A70850CJD",
    "Monday_13": "C0A6EUJNUCB",
    "Monday_14": "C0A6HT62B37",
    "Monday_15": "C0A6EUL0RMZ",
    "Monday_16": "C0A6QTXUP1A",
    "Tuesday_9": "C0A708AM3BK",
    "Tuesday_10": "C0A7FKLUSGY",
    "Tuesday_11": "C0A6MAF0LQ2",
    "Tuesday_12": "C0A6EUTET51",
    "Tuesday_13": "C0A65T2A287",
    "Tuesday_14": "C0A7FKU5C3A",
    "Tuesday_15": "C0A65T57G9M",
    "Tuesday_16": "C0A6K9Q8PKQ",
    "Wednesday_9": "C0A6EV0UARZ",
    "Wednesday_10": "C0A7FKY91Q8",
    "Wednesday_11": "C0A6HTP445T",
    "Wednesday_12": "C0A65TBQTF1",
    "Wednesday_13": "C0A6K9V61L6",
    "Wednesday_14": "C0A708TDWMP",
    "Wednesday_15": "C0A6MAV958S",
    "Wednesday_16": "C0A6K9XUTNJ",
    "Thursday_9": "C0A6HTVMQH3",
    "Thursday_10": "C0A65TJVDM5",
    "Thursday_11": "C0A6KA2L93Q",
    "Thursday_12": "C0A6KA4A9FG",
    "Thursday_13": "C0A6HU0GK29",
    "Thursday_14": "C0A6MB509EE",
    "Thursday_15": "C0A6F02EKBM",
    "Thursday_16": "C0A6QUUEFRS",
    "Friday_9": "C0A6KAAATEJ",
    "Friday_10": "C0A6MB8D09G",
    "Friday_11": "C0A6KABEKL6",
    "Friday_12": "C0A65TVT31D",
    "Friday_13": "C0A6QUYSHPE",
    "Friday_14": "C0A7FLM7RG8",
    "Friday_15": "C0A65TZ3ZU7",
    "Friday_16": "C0A709DM43B",
}

SHEET_URL = "https://docs.google.com/spreadsheets/d/1WE4y8-a7Zxb3dEuRp2hQ4O22JYqn9IJwFnB7Xq1ptes/edit?pli=1&gid=0#gid=0"

def send_slack_message(channel_id:str, week_day: str, week_number: int, sheet_url: str) -> dict:
    """
    Send message to slack channel corresponding with given information to help coordinate tour"
    """

    if week_number < 1 or week_number > 10:
        return {
            "status": f"Skipped, tour during week {week_number} not in weeks 1-10"
        }

    try:
        text = f"""@channel You have an upcoming tour on {week_day} (Week {week_number}). Please bold your name
            <{sheet_url}|here> if you can take it or react with a ❌ if you can not. Thanks!"""
    
        slack_client.chat_postMessage(
            channel = channel_id,
            text = text
        )

        return {
            "status": "Message sent to slack channel",
            "channel_id": {channel_id},
            "message": text
        }

    except Exception as e:
        return {
            "status": "Failed to send message",
            "error": str(e),
        }


def get_channel_id(week_day:str, time: int) -> dict:
    """
    This feature is currently under development. Return the given development channel id for now.Ignore other comments.
    Given a day of the week(monday - friday) and a time (9am - 4pm)
    return the slack channel id corresponding to that day/time
    """

    #try:
       # key = week_day + "_" + str(time)
        #channel_id = CHANNEL_MAP[key]
        #return {
            #"channel_id": channel_id,
            #"status": "retrieved channel id",
        #}
    
    #except Exception as e:
       # return {
            #"status": "Unable to retrive channel id",
            #}
    
    return {
        "channel_id": "C0AKSD2DQ06",
        "Status": "Retrieved development channel id"
    }
    
def update_tour_status(event_id: str, status: str) -> dict:
    """
    Update the tour status for a given tour in the django model database
    """

    try:
        tour = Tour.objects.get(event_id = event_id)
        old_status = tour.status
        tour.status = status
        tour.save(update_fields=['status'])

        return {
            "status": "updated tour status",
            "old_status": old_status,
            "new_status": status,
        }
    
    except Tour.DoesNotExist:
        return {
            "status": f"Tour with event_id {event_id} not found"
        }
    except Exception as e:
        return {
            "status": "Failed to update tour status",
            "error": str(e)
        }


def get_sheet_url(week_number: int) -> dict:
    """
    given a week number, extract the corresponding url for that week's google sheet page
    """

    try:

        scopes = [
            "https://www.googleapis.com/auth/spreadsheets"
        ]

        creds_json = os.environ.get("GSHEETS_CREDENTIALS_JSON")
        creds_dict = json.loads(creds_json)
        creds = Credentials.from_service_account_info(creds_dict, scopes=scopes)
        gspread_client = gspread.authorize(creds)


        base_url = "https://docs.google.com/spreadsheets/d/1WE4y8-a7Zxb3dEuRp2hQ4O22JYqn9IJwFnB7Xq1ptes/edit"
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
            "status": "Failed to obtain google sheet url",
            "error": str(e),
        }