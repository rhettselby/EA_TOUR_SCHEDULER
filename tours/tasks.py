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
from dotenv import load_dotenv
load_dotenv()
from .models import Tour

USERNAME = os.environ['BOOKED_USERNAME']
PASSWORD = os.environ['BOOKED_PASSWORD']

@shared_task
def TourScraper():

    OASA_website = 'https://tours.engineering.ucla.edu/Web/index.php?redirect='
    driver = webdriver.Chrome(service=Service(ChromeDriverManager().install()))
    driver.get(OASA_website)

#Sign into OASA Tours Website
    for char in USERNAME:
        driver.find_element(By.ID, "email").send_keys(char)
        time.sleep(.05)
    for char in PASSWORD:
        driver.find_element(By.ID, "password").send_keys(char)
        time.sleep(.05)

    
#Click Login, had to use XPath to get it to work
    driver.find_element(By.XPATH, "//button[@type='submit']").click()


#wait ten seconds to ensure next page loads
    print("waiting to sign in")
    WebDriverWait(driver, 10).until(
        EC.presence_of_element_located((By.ID, "announcements-dashboard"))
    )

#navigate to tours schedule
    tour_schedule_website = 'https://tours.engineering.ucla.edu/Web/schedule.php?&sfw=1'
    driver.get(tour_schedule_website)

#wait for schedule to render
    WebDriverWait(driver, 10).until(
        EC.presence_of_element_located((By.CLASS_NAME, "event"))
    )


#grab html from website
    current_week_html = driver.page_source
    print("loaded html")

    driver.quit()

    print(current_week_html.count('class="reserved event"'))

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

            #Get data-resid to use an unique identifier
            event_id = event.get("data-resid")

            #determine if group tour
            group_tour = 'Group Tour' in event.get_text(strip=True)

            if event_id in result:
                result[event_id][2] += 1
            else:
                result[event_id] = [start_dt, end_dt, 1, group_tour]

        

    for event_id, info in result.items():
        if info[3]:
            event_id = f"GROUP_TOUR at_{info[0]}"
    
        _, created = Tour.objects.get_or_create(
            event_id=event_id,
            defaults={
                "start_dt":info[0],
                "end_dt":info[1],
                "number_of_guests":info[2],
                "group_tour":info[3],
            }
        )

