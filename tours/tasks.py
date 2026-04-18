from zoneinfo import ZoneInfo
from celery import shared_task
from datetime import datetime
from datetime import timezone
import time
import os
from bs4 import BeautifulSoup
import pytz
from selenium import webdriver
from selenium.webdriver.chrome.service import Service
from webdriver_manager.chrome import ChromeDriverManager
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.common.by import By
from selenium.webdriver.chrome.options import Options
from dotenv import load_dotenv
load_dotenv()
from .models import Guest, Tour
from gsheets.services import update_sheet
USERNAME = os.environ.get('BOOKED_USERNAME')
PASSWORD = os.environ.get('BOOKED_PASSWORD')
#Ai Agent
from agents.utils import run_agent
import asyncio
#moved chrome driver install outside of function so runs
#once each time celery starts up, not every time it runs task
CHROME_DRIVER_PATH = ChromeDriverManager().install()
from django.utils import timezone as dj_timezone 


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
        print(f"sending message to {number}")
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

##### Cancellation Function #####
def cancellations_api(events):
    try:
        active_guests = Guest.objects.exclude(past_event=True)
        count = 0
        for guest in active_guests:
            if guest.event_id not in events and guest.group_tour == False:

                #check if tour exists for this guest
                tour = guest.tour
                if not tour:
                    print(f"Tour not found for {guest.guest_name}")
                    continue
                
                #logic to fix same day cancellations bug (compares using UTC)
                start_dt = tour.start_dt
                if start_dt < dj_timezone.now():
                    print(f"Unable to cancell past event for {tour.guest_name}")
                    continue

                #remove guest from tour
                names = tour.guest_name
                if guest.guest_name in tour.guest_name:
                    names.remove(guest.guest_name)
                    print(f"removed {guest.guest_name} from tour {tour.event_id}")
                tour.guest_name = names

                #No other guests in tour
                if not names:  
                    print(f"Tour {tour.event_id} cancelled")      
                    #call notficy cancellation async
                    pst = pytz.timezone('America/Los_Angeles')
                    start_dt_pst = start_dt.astimezone(pst)
                    week_day = start_dt_pst.strftime("%A")
                    time_str = start_dt_pst.strftime("%-I:%M %p")
                    notify_cancellation.delay(tour.event_id, guest.guest_name, time_str, tour.week_number, week_day)
                    count += 1
                    tour.delete()
                else:
                    tour.save()
                
                guest.delete()

        print (f"{count} tours cancelled")

    except Exception as e:
        print(f"Error cancelling tour: {e}")
        


@shared_task
def notify_cancellation(event_id, guest_name, time_str, week_number, week_day):

    query = f"""Notify guides that tour {event_id} at {time_str} on {week_day} during week {week_number} has been cancelled for {guest_name}. Please
    handle this cancellation by delegating to the cancellation agent and providing the event_id, time, week number, guest name, and week day.
    """
    asyncio.run(run_agent(query, event_id))
    

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

    guest_count = 0
    tour_count = 0
    for event_id, info in result.items():
        try:
            if info[3]:
                event_id = f"GROUP_TOUR at_{info[0]}"

            #determine week number
            quarter_start_dt = datetime.strptime(quarter_start, '%Y-%m-%d').replace(tzinfo=timezone.utc)
            days = (info[0] - quarter_start_dt).days
            week = days // 7 + 1

            guest, created_guest = Guest.objects.get_or_create(
                event_id=event_id,
                defaults={
                    "start_dt": info[0],
                    "end_dt": info[1],
                    "number_of_guests": info[2],
                    "group_tour": info[3],
                    "guest_name": info[4],
                    "week_number": week,
                    "tour": None,
                }
            )
            # New Guest Created
            if created_guest:
                guest_count += 1
                tour, created_tour = Tour.objects.get_or_create(
                    start_dt = info[0],
                    defaults={
                    "event_id" : event_id,
                    "end_dt": info[1],
                    "number_of_guests": info[2],
                    "group_tour": info[3],
                    "guest_name": [info[4]],
                    "week_number": week,
                    }
                )

                # Tour already exists, add new Guest to tour
                if not created_tour:
                    tour.guest_name.append(info[4])
                    tour.number_of_guests += info[2] 
                    tour.save()
    
                
                #New Tour created
                else:
                    tour_count += 1
                    #call agent first, so call doesnt depend on update_sheet success
                    run_agent_celery.delay(event_id, week)
                    update_sheet(info[0], info[3])
                    send_text(info[0], info[3])
                
                guest.tour = tour
                guest.save()


        except Exception as e:
            print(f"failed to process event {event_id} ({info[4]}), error: {e}")
    
    print(f"{guest_count} new guests, {tour_count} new tours.")
    try:
        #check each event_id in database still on website
        cancellations_api(result.keys())
        #print("disabled cancellation for now")

    except Exception as e:
        print(f"Failed to check for cancelled events: {e}")

@shared_task
def run_agent_celery(event_id, week):

    tour = Tour.objects.get(event_id=event_id)
    
    #convert to PST
    pst = ZoneInfo("America/Los_Angeles")
    start_dt_pst = tour.start_dt.astimezone(pst)
    time_str = start_dt_pst.strftime("%-I:%M %p")

    #extract day + hour
    week_day = start_dt_pst.strftime('%A')
    

    query = f"Handle this incoming tour with week_day: {week_day}, time: {time_str}, week_number: {week}, event_id: {event_id}, and status: unassigned. Delegate work to slack_agent"
    asyncio.run(run_agent(query, event_id))