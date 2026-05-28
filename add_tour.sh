#!/bin/bash
# Manually add a tour + guest record to the database.
# Run from the project root: bash add_tour.sh

set -e
cd "$(dirname "$0")"

echo ""
echo "=== Add Tour ==="
echo ""

read -p "Guest name: "                    GUEST_NAME
read -p "Date (YYYY-MM-DD, PST): "        DATE
read -p "Start time (HH:MM, 24h PST): "  START_TIME
read -p "Duration in minutes [60]: "      DURATION
read -p "Number of guests [1]: "          NUM_GUESTS
read -p "Group tour? (y/n) [n]: "         IS_GROUP

DURATION=${DURATION:-60}
NUM_GUESTS=${NUM_GUESTS:-1}
IS_GROUP=${IS_GROUP:-n}

# Activate venv if present
if [ -f "venv/bin/activate" ]; then
  source venv/bin/activate
fi

# Pass inputs as env vars to avoid shell-quoting issues inside Python
export TOUR_GUEST_NAME="$GUEST_NAME"
export TOUR_DATE="$DATE"
export TOUR_START_TIME="$START_TIME"
export TOUR_DURATION="$DURATION"
export TOUR_NUM_GUESTS="$NUM_GUESTS"
export TOUR_IS_GROUP="$IS_GROUP"

python manage.py shell -c "
import os
from datetime import datetime, timedelta
from zoneinfo import ZoneInfo
from tours.models import Tour, Guest

# --- Read inputs ---
guest_name  = os.environ['TOUR_GUEST_NAME']
date_str    = os.environ['TOUR_DATE']
time_str    = os.environ['TOUR_START_TIME']
duration    = int(os.environ['TOUR_DURATION'])
num_guests  = int(os.environ['TOUR_NUM_GUESTS'])
is_group    = os.environ['TOUR_IS_GROUP'].strip().lower() in ('y', 'yes')

# --- Parse datetime in PST, convert to UTC for storage ---
pst = ZoneInfo('America/Los_Angeles')
start_pst = datetime.strptime(f'{date_str} {time_str}', '%Y-%m-%d %H:%M').replace(tzinfo=pst)
start_utc = start_pst.astimezone(ZoneInfo('UTC'))
end_utc   = start_utc + timedelta(minutes=duration)

# --- Calculate week number from QUARTER_START_DATE ---
quarter_start_str = os.environ.get('QUARTER_START_DATE')
if quarter_start_str:
    from datetime import timezone as tz
    qs = datetime.strptime(quarter_start_str, '%Y-%m-%d').replace(tzinfo=tz.utc)
    week = (start_utc - qs).days // 7 + 1
else:
    week = 1
    print('Warning: QUARTER_START_DATE not set, defaulting to week 1')

# --- Build event_id (mirrors scraper format) ---
ts = int(start_utc.timestamp())
if is_group:
    event_id = f'Group_tour_at_{ts}'
else:
    import random
    event_id = f'MANUAL_{ts}_{random.randint(1000, 9999)}'

# --- Create or update Tour ---
tour, tour_created = Tour.objects.get_or_create(
    start_dt=start_utc,
    defaults={
        'event_id':        event_id,
        'end_dt':          end_utc,
        'number_of_guests': num_guests,
        'group_tour':      is_group,
        'guest_name':      [guest_name],
        'week_number':     week,
        'status':          'unassigned',
    }
)

if not tour_created:
    if guest_name not in tour.guest_name:
        tour.guest_name.append(guest_name)
    tour.number_of_guests += num_guests
    tour.save()

# --- Create Guest ---
guest, guest_created = Guest.objects.get_or_create(
    event_id=event_id,
    defaults={
        'start_dt':        start_utc,
        'end_dt':          end_utc,
        'number_of_guests': num_guests,
        'group_tour':      is_group,
        'guest_name':      guest_name,
        'week_number':     week,
        'tour':            tour,
    }
)

if not guest_created:
    guest.tour = tour
    guest.save()

# --- Summary ---
label = start_pst.strftime('%a %b %d at %I:%M %p %Z')
kind  = 'Group tour' if is_group else 'Tour'
print()
if tour_created:
    print(f'Created {kind}: {label} (Week {week})')
else:
    print(f'Added {guest_name} to existing tour at {label}')
if guest_created:
    print(f'Guest record created: {guest_name}')
else:
    print(f'Guest record already existed: {guest_name}')
print(f'Tour ID:   {tour.id}')
print(f'Event ID:  {tour.event_id}')
print(f'Status:    {tour.status}')
print()
"
