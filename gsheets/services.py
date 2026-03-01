from zoneinfo import ZoneInfo

import gspread
from google.oauth2.service_account import Credentials

import os

from datetime import datetime, timezone

from datetime import timedelta

BASE_DIR = os.path.dirname(os.path.abspath(__file__))



quarter_start = os.environ.get("QUARTER_START_DATE")

def update_sheet(tour_start_dt, is_group_tour):

    ##### Sheet set up #####

    scopes = [
        "https://www.googleapis.com/auth/spreadsheets"
    ]

    creds = Credentials.from_service_account_file(os.path.join(BASE_DIR, "credentials.json"), scopes=scopes)

    client = gspread.authorize(creds)

    sheet_id = "1WE4y8-a7Zxb3dEuRp2hQ4O22JYqn9IJwFnB7Xq1ptes"

    sheet = client.open_by_key(sheet_id)


    ##### Extract week, day, hour

    #timezone aware
    quarter_start_dt = datetime.strptime(quarter_start, '%Y-%m-%d').replace(tzinfo=timezone.utc)

    days = (tour_start_dt - quarter_start_dt).days
    week = days // 7

    # Correspond day of week
    pst_dt = tour_start_dt.astimezone(ZoneInfo("America/Los_Angeles"))
    day = pst_dt.weekday()

    #hour
    hour = pst_dt.hour

    
    ##### Update corresponding cells

    worksheet = None

    try:
        worksheet = sheet.worksheet(f"Week {week + 1}")

    except:
        worksheet = sheet.get_worksheet(week + 1)
    

    starting_row = 3 + (hour - 9) * 4

    #invalid start time
    if not 2 < starting_row < 32:
        raise ValueError("Invalid Start Time")

    column = day + 2
    
    #invalid day
    if not 1 < column < 7:
        raise ValueError("Invalid Day of Week")

    A1_top = gspread.utils.rowcol_to_a1(starting_row, column)
    A1_bottom = gspread.utils.rowcol_to_a1(starting_row + 3, column)

    A1_range = A1_top + ":" + A1_bottom

    if is_group_tour:
        color = {"red": 1, "green": 0.9490196, "blue": 0.8}
    else:
        color = {"red": 0.7882353, "green": 0.85490197, "blue": 0.972549}

    worksheet.format(A1_range, {"backgroundColor": color})
    










    




