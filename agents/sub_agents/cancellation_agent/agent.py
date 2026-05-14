# agents/sub_agents/cancellation_agent/agent.py
from google.adk.agents.llm_agent import Agent
from agents.tools.cancellation_tools import slack_cancellation
from google.adk.models.lite_llm import LiteLlm

cancellation_agent = Agent(
    model=LiteLlm(model="claude-sonnet-4-6"),
    name='cancellation_agent',
    description="Handles tour cancellations by sending cancellation notification to the appropriate slack channel",
    instruction="""You handle tour cancellations. Your job is to take the event_id you have been given and use the slack_cancellation tool
        to send a slack message notifying of the cancelled tour.
    """,
    tools=[slack_cancellation],
)

cancellation_agent_fallback = Agent(
    model=LiteLlm(model="claude-sonnet-4-20250514"),
    name='cancellation_agent_fallback',
    description="Fallback agent for when cancellation agent fails to run. Handles tour cancellations by sending cancellation notification to the appropriate slack channel",
    instruction="""You handle tour cancellations. Your job is to take the event_id you have been given and use the slack_cancellation tool
        to send a slack message notifying of the cancelled tour.
    """,
    tools=[slack_cancellation],
)