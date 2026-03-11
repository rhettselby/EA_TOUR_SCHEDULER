# agents/sub_agents/cancellation_agent/agent.py
from google.adk.agents.llm_agent import Agent

cancellation_agent = Agent(
    model='gemini-2.0-flash-lite',
    name='cancellation_agent',
    description="Handles tour cancellations",
    instruction="You handle tour cancellations. This agent is not yet implemented.",
    tools=[],
)