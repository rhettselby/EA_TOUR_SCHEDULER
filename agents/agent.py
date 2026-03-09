from google.adk.agents.llm_agent import Agent
from .sub_agents.slack_agent.agent import slack_agent
from .sub_agents.cancellation_agent.agent import cancellation_agent

root_agent = Agent(
    model='gemini-2.0-flash',
    name='root_agent',
    description="Delegates work to appropriate sub-agent",
    instruction="You are the lead agent, responsible for delegating work to your sub-agents",
    tools=[],
    agents=[slack_agent, cancellation_agent]
)

