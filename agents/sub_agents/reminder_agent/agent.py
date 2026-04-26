from google.adk.agents.llm_agent import Agent
from google.adk.models.lite_llm import LiteLlm
#from agents.tools.reminder_tools import ...


slack_agent = Agent(
    model='gemini-2.5-flash',
    name='reminder_agent',
    description= """sends reminders for upcoming tours or other required actions""",
    instruction = "",
)