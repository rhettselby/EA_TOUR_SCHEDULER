# agents/sub_agents/cancellation_agent/agent.py
from google.adk.agents.llm_agent import Agent
from agents.tools.cancellation_tools import get_channel_id, slack_cancellation
from google.adk.models.lite_llm import LiteLlm

cancellation_agent = Agent(
    model=LiteLlm(model="claude-sonnet-4-6"),
    name='cancellation_agent',
    description="Handles tour cancellations by sending cancellation notification to the appropriate slack channel",
    instruction="""You handle tour cancellations. Your job is to take the event_id you have been given, obtain the 
     correct channel_id using the gen_channel_id tool and use the slack_cancellation tool to send a slack message to the obtained channel
        to send a slack message notifying of the cancelled tour.

        You have the following tools available, you must get the channel_id before sending the slack message:

        1. get_channel_id(week_day:str, time: int)
            -given a day of the week (mon-fri) and a time (e.g. 1pm), obtain the proper channel id for that time slot
            from the channel_id mapping
        
        2. slack_cancellation(channel_id:str, time:str, guest_name:str, week_number:int, week_day: str)
         - send the slack cancellation message to the obtained channel
    """,
    tools=[get_channel_id, slack_cancellation],
)
