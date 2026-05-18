import asyncio
from celery import shared_task
from agents.utils import run_agent
from tours.models import Tour


@shared_task
def run_slack_agent(channel, text, time_stamp):
    try:
        print("sending slack_agent message")
        query = f"A message was sent in slack at {time_stamp}. Please respond to the following message in channel {channel}: {text}"
        asyncio.run(run_agent(query, channel))
    except Exception as e:
        print(str(e))
