from zoneinfo import ZoneInfo
from celery import shared_task
from datetime import datetime
from datetime import timezone
import time
import os
from bs4 import BeautifulSoup
from selenium import webdriver
from selenium.webdriver.chrome.service import Service
from webdriver_manager.chrome import ChromeDriverManager
from selenium.webdriver.support.ui import WebDriverWait, Select
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.common.by import By
from selenium.webdriver.chrome.options import Options
from dotenv import load_dotenv
load_dotenv()
from .models import Tour
from gsheets.services import update_sheet
USERNAME = os.environ.get('BOOKED_USERNAME')
PASSWORD = os.environ.get('BOOKED_PASSWORD')



from twilio.rest import Client


####Automatic Texts sent by Twilio #####

DOT_NUMBERS = ['+18052456513', '+16196369384', '+16106205106']

def send_text(start_dt, group_tour):

    account_sid = os.environ["TWILIO_ACCOUNT_SID"]
    auth_token  = os.environ["TWILIO_AUTH_TOKEN"]

    pst_dt = start_dt.astimezone(ZoneInfo("America/Los_Angeles"))
    time_str = pst_dt.strftime('%a %b %d at %I:%M %p %Z')

   
    client = Client(account_sid, auth_token)

    for number in DOT_NUMBERS:
        message = client.messages.create(
         body=f"New group tour added to schedule at {time_str}" if group_tour else \
                f"New tour added to schedule at {time_str}",
            from_="+18773301601", 
            to=number
        )
        print(message.sid)


####Webscraper Function

@shared_task
def TourScraper():
    try:
        #Login Page
        OASA_website = 'https://tours.engineering.ucla.edu/Web/index.php?redirect='

        options = Options()
        options.add_argument("--headless")
        options.add_argument("--no-sandbox")
        options.add_argument("--disable-dev-shm-usage")
        options.add_argument("--single-process")
        options.binary_location = "/usr/bin/google-chrome"

        driver = webdriver.Chrome(
            service=Service(ChromeDriverManager().install()),
            options=options
        )
        driver.get(OASA_website)

        for char in USERNAME:
            driver.find_element(By.ID, "email").send_keys(char)
            time.sleep(.05)
        for char in PASSWORD:
            driver.find_element(By.ID, "password").send_keys(char)
            time.sleep(.05)

        button = driver.find_element(By.XPATH, "//button[@type='submit']")
        driver.execute_script("arguments[0].click();", button)



        print("waiting to sign in")
        try:
            WebDriverWait(driver, 30).until(
                EC.presence_of_element_located((By.ID, "announcements-dashboard"))
            )
        except:
            print("TIMEOUT - current URL:", driver.current_url)
            print("PAGE SOURCE:", driver.page_source[:1000])
            return

        #Schedule Page
        tour_schedule_website = 'https://tours.engineering.ucla.edu/Web/schedule.php?&sfw=1'
        driver.get(tour_schedule_website)

        WebDriverWait(driver, 10).until(
            EC.presence_of_element_located((By.CLASS_NAME, "event"))
        )

        #Select 10-day period view

        button = driver.find_element(By.ID, "change-visible-days-btn")
        driver.execute_script("arguments[0].click();", button)

        #select "10" from dropdown
        select_element = driver.find_element(By.ID, "visible-days-select")
        select = Select(select_element)
        select.select_by_value("10")
        time.sleep(2)
        
        WebDriverWait(driver, 10).until(
            EC.presence_of_element_located((By.CLASS_NAME, "event"))
        )

        current_week_html = driver.page_source
        print("loaded html")

    #ensure driver always quits
    finally:
        driver.quit()

    soup = BeautifulSoup(current_week_html, 'lxml')
    tours = [e for e in soup.find_all('div', class_="reserved") if 'past' not in e.get('class', [])]
    group_tours = [e for e in soup.find_all('div', class_="unreservable") if 'past' not in e.get('class', []) and 'Group Tour' in e.get_text(strip=True)]
    events = tours + group_tours

    print("retrieved tours")
    result = {}
    for event in events:
        if event.get("data-start"):
            start_ts = int(event.get("data-start"))
            end_ts = int(event.get("data-end"))
            start_dt = datetime.fromtimestamp(start_ts, tz=timezone.utc)
            end_dt = datetime.fromtimestamp(end_ts, tz=timezone.utc)
            event_id = event.get("data-resid")
            group_tour = 'Group Tour' in event.get_text(strip=True)
            guest_name = event.get_text(strip=True)

            if event_id in result:
                result[event_id][2] += 1
            else:
                result[event_id] = [start_dt, end_dt, 1, group_tour, guest_name]

    for event_id, info in result.items():
        if info[3]:
            event_id = f"GROUP_TOUR at_{info[0]}"
        _, created = Tour.objects.get_or_create(
            event_id=event_id,
            defaults={
                "start_dt": info[0],
                "end_dt": info[1],
                "number_of_guests": info[2],
                "group_tour": info[3],
                "guest_name": info[4],
            }
        )
        if created:
            #send_text(info[0], info[3])
            update_sheet(info[0], info[3])

