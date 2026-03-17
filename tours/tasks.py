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
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.common.by import By
from selenium.webdriver.chrome.options import Options
from dotenv import load_dotenv
load_dotenv()
from .models import Tour
from gsheets.services import update_sheet
USERNAME = os.environ.get('BOOKED_USERNAME')
PASSWORD = os.environ.get('BOOKED_PASSWORD')
#Ai Agent
from agents.utils import run_agent
import asyncio

#moved chrome driver install outside of function so runs
#once each time celery starts up, not every time it runs task
CHROME_DRIVER_PATH = ChromeDriverManager().install()


from twilio.rest import Client

quarter_start = os.environ.get('QUARTER_START_DATE')


####Automatic Texts sent by Twilio #####

DOT_NUMBERS = ['+18052456513']

def send_text(start_dt, group_tour):

    account_sid = os.environ["TWILIO_ACCOUNT_SID"]
    auth_token  = os.environ["TWILIO_AUTH_TOKEN"]

    pst_dt = start_dt.astimezone(ZoneInfo("America/Los_Angeles"))
    time_str = pst_dt.strftime('%a %b %d at %I:%M %p %Z')

   
    client = Client(account_sid, auth_token)

    for number in DOT_NUMBERS:
        try:
            body=f"New group tour added to schedule" if group_tour else f"New tour added to schedule"
            body += f" at {time_str}"
            message = client.messages.create(
                body=body,
                from_="+16562700475", 
                to=number,
            )
            print(message.sid)

        except Exception as e:
            print(f"failed to send message, error: {e}")


####Webscraper Function

@shared_task
def TourScraper():
    try:
        OASA_website = 'https://tours.engineering.ucla.edu/Web/index.php?redirect='

        options = Options()
        options.add_argument("--headless")
        options.add_argument("--no-sandbox")
        options.add_argument("--disable-dev-shm-usage")
        options.binary_location = "/usr/bin/google-chrome"

        driver = webdriver.Chrome(
            service=Service(CHROME_DRIVER_PATH),
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

        tour_schedule_website = 'https://tours.engineering.ucla.edu/Web/schedule.php?dv=14'
        driver.get(tour_schedule_website)

        WebDriverWait(driver, 30).until(
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

            # def next (iterator, default):
            existing = next((id for id, info in result.items() if info[0] == start_dt and info[4] == guest_name), None)

            #tour already found
            if event_id in result:
                result[event_id][2] += 1
            #same time + guest name as existing tour
            elif existing:
                result[existing][2] += 1
            #found new tour
            else:
                result[event_id] = [start_dt, end_dt, 1, group_tour, guest_name]

    for event_id, info in result.items():
        try:
            if info[3]:
                event_id = f"GROUP_TOUR at_{info[0]}"

            #determine week number
            quarter_start_dt = datetime.strptime(quarter_start, '%Y-%m-%d').replace(tzinfo=timezone.utc)
            days = (info[0] - quarter_start_dt).days
            week = days // 7 + 1

            _, created = Tour.objects.get_or_create(
                event_id=event_id,
                defaults={
                    "start_dt": info[0],
                    "end_dt": info[1],
                    "number_of_guests": info[2],
                    "group_tour": info[3],
                    "guest_name": info[4],
                    "week_number": week,
                    "status": "unassigned",
                }
            )
            if created:
                #call agent first, so call doesnt depend on update_sheet success
                run_agent_celery.delay(event_id, week)
                update_sheet(info[0], info[3])
                send_text(info[0], info[3])
        except Exception as e:
            print(f"failed to process event {event_id} ({info[4]}), error: {e}")

@shared_task
def run_agent_celery(event_id, week):

    tour = Tour.objects.get(event_id=event_id)
    
    #convert to PST
    pst = ZoneInfo("America/Los_Angeles")
    start_dt_pst = tour.start_dt.astimezone(pst)

    #extract day + hour
    week_day = start_dt_pst.strftime('%A')
    hour = start_dt_pst.hour 

    query = f"Handle this incoming tour with week_day: {week_day}, time: {hour}, week_number: {week}, event_id: {event_id}, and status: unassigned. Delegate work to slack_agent"
    asyncio.run(run_agent(query, event_id))

