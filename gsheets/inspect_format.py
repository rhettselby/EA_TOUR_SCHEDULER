

import gspread
from google.oauth2.service_account import Credentials

import os


from gspread_formatting import get_effective_format


quarter_start = os.environ.get("QUARTER_START_DATE")

def update_sheet():

    ##### Sheet set up #####

    scopes = [
        "https://www.googleapis.com/auth/spreadsheets"
    ]

    creds = Credentials.from_service_account_file("credentials.json", scopes = scopes)

    client = gspread.authorize(creds)

    sheet_id = "1WE4y8-a7Zxb3dEuRp2hQ4O22JYqn9IJwFnB7Xq1ptes"

    sheet = client.open_by_key(sheet_id)

    
    ##### Update corresponding cells

    worksheet = sheet.get_worksheet(9)


    fmt = get_effective_format(worksheet, 'E17')

    print(fmt)
    
if __name__=="__main__":
    update_sheet()









    




