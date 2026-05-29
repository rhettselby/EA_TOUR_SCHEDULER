import os
from slack_sdk import WebClient

import pytz
#gsheets


CANCELLATION_CHANNEL_ID = "C0AKSD2DQ06"


CHANNEL_MAP = {
    "Monday_9": "C0AM295E423",
    "Monday_10": "C0ANC0ZFZFA",
    "Monday_11": "C0AM29D94AK",
    "Monday_12": "C0AMWKWJPB3",
    "Monday_13": "C0AMEA95ABF",
    "Monday_14": "C0AMHSR6EV8",
    "Monday_15": "C0AMMAP03M2",
    "Monday_16": "C0AMFM88XGW",
    "Tuesday_9": "C0AMHP0F0SW",
    "Tuesday_10": "C0AMFN16BF0",
    "Tuesday_11": "C0AM29XE6G7",
    "Tuesday_12": "C0AMWLFMRMF",
    "Tuesday_13": "C0AMHPARKBL",
    "Tuesday_14": "C0AMBBY8K2P",
    "Tuesday_15": "C0AM2A7RK2B",
    "Tuesday_16": "C0AMWLRAVFT",
    "Wednesday_9": "C0AMVQUSLQZ",
    "Wednesday_10": "C0AMGTR96E6",
    "Wednesday_11": "C0AMAGCQSCT",
    "Wednesday_12": "C0AMLFQRZU4",
    "Wednesday_13": "C0AMGTZK6UA",
    "Wednesday_14": "C0AMESE6BEJ",
    "Wednesday_15": "C0AMDFRC8PP",
    "Wednesday_16": "C0AMGU86V3L",
    "Thursday_9": "C0AMAGWRQAF",
    "Thursday_10": "C0ANB7394KS",
    "Thursday_11": "C0AM1FD6N23",
    "Thursday_12": "C0AMDG7SG7P",
    "Thursday_13": "C0AMGURQS3C",
    "Thursday_14": "C0AMLGMQ2EQ",
    "Thursday_15": "C0AMVS6N29F",
    "Thursday_16": "C0ANB7M5HL0",
    "Friday_9": "C0ANC2XNCQG",
    "Friday_10": "C0AM2B5D3F1",
    "Friday_11": "C0ANC31RSN4",
    "Friday_12": "C0AMHQNAFL2",
    "Friday_13": "C0AM2BJ5F3R",
    "Friday_14": "C0AMECNMZ8D",
    "Friday_15": "C0ANC3G4H4G",
    "Friday_16": "C0AM2BR5ZRD",
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