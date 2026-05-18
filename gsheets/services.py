from zoneinfo import ZoneInfo

import gspread
from google.oauth2.service_account import Credentials

import os

from datetime import datetime, timezone

from datetime import timedelta

import json



quarter_start = os.environ.get("QUARTER_START_DATE")
from asgiref.sync import sync_to_async

async def update_sheet(tour_start_dt, is_group_tour, cancellation):
    print("Update sheet called")

    def _update():
        ##### Sheet set up #####
        scopes = [
            "https://www.googleapis.com/auth/spreadsheets"
        ]

        creds_json = os.environ.get("GSHEETS_CREDENTIALS_JSON")
        creds_dict = json.loads(creds_json)
        creds = Credentials.from_service_account_info(creds_dict, scopes=scopes)

        client = gspread.authorize(creds)

        sheet_id = "1_rOWH5jgSI15TUSmzJ4MMtnqHqG5wdu1_K7AcjYT9MM"
        sheet = client.open_by_key(sheet_id)

        ##### Extract week, day, hour
        quarter_start_dt = datetime.strptime(quarter_start, '%Y-%m-%d').replace(tzinfo=timezone.utc)
        days = (tour_start_dt - quarter_start_dt).days
        week = days // 7

        pst_dt = tour_start_dt.astimezone(ZoneInfo("America/Los_Angeles"))
        day = pst_dt.weekday()
        hour = pst_dt.hour

        ##### Update corresponding cells
        worksheet = None
        try:
            worksheet = sheet.worksheet(f"Week {week + 1}")
        except:
            worksheet = sheet.get_worksheet(week + 1)

        starting_row = 3 + (hour - 9) * 4

        if not 2 < starting_row < 32:
            raise ValueError("Invalid Start Time")

        column = day + 2

        if not 1 < column < 7:
            raise ValueError("Invalid Day of Week")

        A1_top = gspread.utils.rowcol_to_a1(starting_row, column)
        A1_bottom = gspread.utils.rowcol_to_a1(starting_row + 3, column)
        A1_range = A1_top + ":" + A1_bottom

        if not cancellation:
            print("Google Sheet background updated for tour")
            if is_group_tour:
                color = {"red": 1, "green": 0.9490196, "blue": 0.8}
            else:
                color = {"red": 0.7882353, "green": 0.85490197, "blue": 0.972549}

            worksheet.format(A1_range, {"backgroundColor": color})
        else:
            print("Google Sheet background removed for cancellation")
            worksheet.format(A1_range, {"backgroundColor": {"red": 1, "green": 1, "blue": 1}})
            
    await sync_to_async(_update)()









    




