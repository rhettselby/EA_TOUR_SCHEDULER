# EA Tour Scheduler

## Overview

As the director of tours for UCLA Engineering Ambassadors, it is my responsibility to coordinate the tours of the engineering school that are provided by my club. This job can be tedious and requires constant attention to the UCLA tour website. For this reason I decided to build a project that automates some of this work.

The first feature I implemented was a Selenium/BeautifulSoup web scraper. The schedule runs on ScheduleIt, which supposedly has a public API, but I could not figure out how to access it (web scraping is more fun). Scraped tours are persisted to a Postgres database via Django, hosted by Railway. A simple React frontend displays the schedule and each tour's status. Lastly, I designed an AI agent system that sends Slack messages via the Slack API for each incoming tour, and uses the Google Sheets API to automate that coordination.

## System Architecture

1. **Web Process (Django + gunicorn)**
   - Serves the React dashboard and the REST API inside a single process

2. **Background Workers (Celery)**
   - Runs asynchronous tasks scheduled by Celery Beat
   - Allows for separation of the web process and async tasks
   - Supports an independent-task model
   - Up to 4 parallel workers

3. **The Scheduler (Celery Beat)**
   - Drops tasks onto the queue on a schedule

4. **Broker + Result Backend (Redis)**

5. **Database (Postgres)**

## Web Scraping

Selenium and BeautifulSoup perform two distinct jobs. Selenium extracts the HTML by running a headless Chrome browser; BeautifulSoup parses that extracted HTML for specific elements.

**Selenium** — drives a headless Chrome browser, logs in, clicks, waits for JavaScript to execute, and collects the HTML. Headless is required because in production it runs in a Linux container on Railway that has no display at all, and a headed browser would also be less resource-efficient.

```python
driver = webdriver.Chrome(
    service=Service(CHROME_DRIVER_PATH),
    options=options
)
driver.set_page_load_timeout(60)
driver.get(OASA_website)
```

Login is automated: Selenium types the username/password character by character (with a delay to help avoid bot detection) and clicks submit, then waits for a known element to appear before proceeding.

**BeautifulSoup** — an HTML parser that makes it easy to search and extract elements from the HTML.

```python
soup = BeautifulSoup(current_week_html, 'lxml')
tours = [e for e in soup.find_all('div', class_="reserved") if 'past' not in e.get('class', [])]
group_tours = [e for e in soup.find_all('div', class_="unreservable") if 'past' not in e.get('class', []) and 'Group Tour' in e.get_text(strip=True)]
events = tours + group_tours
```

Regular tours are parsed via `reserved` divs, while group tours are parsed via `unreservable` divs. Past tours are filtered out, and I also collect start times, `data-resid` (a unique identifier), and other guest information.

While web scraping is a more fragile strategy for retrieving tours than using a public API, I decided that it is unlikely UCLA will change their website in the near future. In the case that it was changed, my scraping task uses `try`/`except` blocks so errors are caught and logged gracefully, Selenium has a timeout, and I would quickly notice a lack of tours on the frontend. Ultimately, I had a lot of fun building my first web scraper.

## Database

I use a Postgres database to persist the tours found by the web scraper. I chose Postgres since Railway provides a built-in Postgres service. (Locally, development uses SQLite.)

There are two models in my database, `Tour` and `Guest`:

```python
class Tour(models.Model):
    event_id = models.CharField(unique=True, max_length=255)
    start_dt = models.DateTimeField()
    number_of_guests = models.PositiveIntegerField()
    group_tour = models.BooleanField(default=False)
    week_number = models.PositiveIntegerField(null=True, blank=True)
    ambassador = models.CharField(max_length=255, blank=True, default='')

    STATUS_CHOICES = [
        ('unassigned', 'Unassigned'),
        ('message_sent', 'Message Sent'),
        ('confirmed', 'Confirmed'),
        ('past_event', 'Past Event'),
        ('cancelled', 'Tour Cancelled'),
    ]

    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='unassigned')


class Guest(models.Model):
    event_id = models.CharField(unique=True, max_length=255)
    start_dt = models.DateTimeField()
    guest_name = models.CharField()
    tour = models.ForeignKey(Tour, on_delete=models.CASCADE, null=True, blank=True, default=None)
    # ...
```

Originally I only had a `Tour` model, but later implemented the `Guest` model to better support multi-guest tours. The web scraper scrapes for guests and uses the start time to either add them to an existing tour or create a new tour. Each `Guest` has a foreign key to its tour. If a guest cancels their tour, the backend checks whether they are the only guest belonging to that tour, and if so delegates to the cancellation agent. When a tour is deleted, its guests are automatically deleted as well, due to `on_delete=CASCADE`.

While the `Guest` and `Tour` models store some duplicate information, this is due to legacy code (from before the `Guest` model existed) and for convenient access when retrieving a tour's information.

## AI Agent Network

The network consists of a root agent whose job is only to delegate tasks, a Slack agent that handles new tours, and a cancellation agent that handles cancellations. I plan to implement additional agents in the future.

### Persistence

Messages/responses from the agent are persisted to my Postgres database and grouped together by session. Each session has a unique `USER_ID`, which for tour scheduling ends up being the `event_id` from each tour. Thus each tour has its own conversation history saved to the database. (For general Slack replies, the `USER_ID` is instead the channel ID, so each channel also gets its own history.)

```python
APP_NAME = "TOUR_SCHEDULER"
USER_ID = event_id

db_url = os.environ.get("DATABASE_URL")

session_service = DatabaseSessionService(db_url=db_url)
initial_state = {
    "name": "Rhett",
}

existing_sessions = await session_service.list_sessions(
    app_name=APP_NAME,
    user_id=USER_ID,
)
```

After retrieving a session, a `Runner` selects the agent and provides the session to be run in `run_agent_async`.

```python
runner = Runner(
    agent=root_agent,
    app_name=APP_NAME,
    session_service=session_service
)
```

### Tools

Tools are functions that take arguments (and must specify a return type), execute logic, and return a dictionary of information. It is important to return information that is as comprehensive as possible to ensure the agent interprets the results properly — the docstring and return payload are effectively the interface the model sees.

I first wrote a tool to retrieve the correct Slack channel ID. Since each member of my engineering club is assigned to several time slots throughout the week, with each time slot having its own Slack channel, I had to ensure the agent sent the Slack message to the correct channel for a given tour.

```python
def get_channel_id(week_day: str, time: int) -> dict:
    """
    Given a day of the week (monday - friday) and a time (9am - 4pm)
    return the slack channel id corresponding to that day/time
    """
    try:
        key = week_day + "_" + str(time)
        channel_id = CHANNEL_MAP[key]
        return {
            "channel_id": channel_id,
            "status": "retrieved channel id",
        }
    except Exception as e:
        return {
            "status": "Unable to retrieve channel id",
        }
```

I implemented several other tools that allow the agent to send Slack messages and update the club's Google Sheet schedule.

In order for the AI agent to send Slack messages, you must first create a Slack app (bot) at [api.slack.com](https://api.slack.com). I added the following bot scopes: `chat:write`, `channels:read`. Then I installed the app to my Slack workspace and added the bot token to my environment file. Lastly, I invited the Slack bot to each channel in my workspace that I wanted it to interact with.

Currently the agent retrieves the Slack channel ID for the corresponding day/time via `CHANNEL_MAP`, which is hardcoded. I have to update this once every quarter when we create new channels — something I would possibly automate in the future.

I also have tools dedicated to maintaining the club's Google Sheet schedule. I use a service account, which allows the agent to call the Google API. `update_sheet` is an async function, but `gspread` makes synchronous HTTP calls, so I wrap the sheet work in `sync_to_async`, offloading the I/O to a thread so the event loop stays free.

While tours are displayed via the React frontend, members of my club still use the Google Sheet to sign up for a tour and view the schedule.

## REST API + Authentication

- The React `LoginModal` POSTs a username/password to `/api/auth/login/`.
- `login_view` calls Django's `authenticate()` and, on success, creates a token for the user.
- The frontend saves the token in `localStorage` and sends it with every subsequent request.
- Protected endpoints (`update_status`, `delete_tour`, the scrape trigger) are decorated with `@authentication_classes([TokenAuthentication])` and `@permission_classes([IsAuthenticated])`.

In `tours_api` (the view that retrieves tours), the GET is public but limits the data for unauthenticated users:

```python
if not request.user.is_authenticated:
    for tour in data:
        tour.pop('guests', None)
```

Thus anonymous users can see the schedule, but the guests' personal information is stripped out.

## Frontend + Serving

The React app is compiled to static files at Docker build time, and WhiteNoise serves those static files straight from the Django/gunicorn process.

My app serves Django and React as one deployable unit in a single container. There is no CORS in production since the frontend and API are the same origin, and there is only one deployment pipeline instead of two.

**WhiteNoise:** Since Django doesn't serve static files in production on its own, WhiteNoise lets the Python process itself serve the static files.

Since React does client-side routing, I added a fallback route that serves the app when an unknown URL is entered.

## Deployment

- **Dockerfile** (`python:3.13-slim`) that installs Chrome and Node/npm, pip-installs requirements, and builds the React app.
- **Procfile:** `migrate && backfill_week_numbers && gunicorn` — runs migrations and a data backfill on every deploy.
- **gunicorn** as the production WSGI server, **Railway** as the platform, with **Postgres + Redis** as managed services.

## Tradeoffs

### 1. LLM vs. Deterministic

My current agent has a relatively fixed workflow that could be implemented as deterministic code. The reasons I decided to implement an agent are:

- The agent can detect misspelling/punctuation errors in tour fields and send the corrected version via Slack, and it can reply to free-form messages in the Slack channels — a task that can't be hardcoded.
- I wanted to learn how to implement an AI agent and use Google ADK (agents are cool).

### 2. Auth Hardening

The public surface only exposes non-sensitive schedule data, and the remaining data is hidden behind authentication that is currently limited to a single admin (me). The practical attack surface is small, which is why I deferred hardening. However, the weaknesses are real: DRF tokens never expire and live in `localStorage` (exposed to XSS), and logout is client-side only. At higher stakes I'd add token expiry and invalidate tokens server-side on logout.

### 3. Hardcoded Config

The `CHANNEL_MAP` and Sheet ID are both hardcoded. The channel map requires updates at the start of every quarter as we create new Slack channels. This is something that could be automated, but for now a hardcoded mapping was the simplest approach. If this project grew, I'd move it to a database table editable from the Django admin, so it changes without touching the code.
