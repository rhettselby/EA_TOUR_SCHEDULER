import asyncio
from celery import shared_task
from rich import _console
from agents.utils import run_agent
from tours.models import Tour


@shared_task
def run_slack_agent(channel, text, time_stamp):
    try:
        print("sending slack_agent message")
        query = f"""GENERAL SLACK REPLY TASK: A message was sent in slack at {time_stamp}. Please respond to the following message in channel {channel}: {text}
            Only respond to the message if the message directly references the slack/tour/bot agent, or the message is part of a longer conversation
            with the slack agent (you). 
            """
        asyncio.run(run_agent(query, channel))
    except Exception as e:
        print(str(e))

