
from google.adk.agents.llm_agent import Agent
from .sub_agents.slack_agent.agent import slack_agent
from .sub_agents.cancellation_agent.agent import cancellation_agent

root_agent = Agent(
    model='gemini-2.5-flash',
    name='root_agent',
    description= "Routes incoming tasks to the appropriate sub-agent",

    instruction = 
    """
    You are the root agent of my tour scheduling software system.
    Your job is to delegate work to the sub-agent that would best handle
    the given work. Here is a list of the available sub-agents.

    1. slack_agent:
        The slack agent is responsible for sending messages in the engineering ambassador slack channel in order
        to coordinate tour assignment within the club. This includes sending an initial message to the appropriate channel 
        when a new tour is recieved, and following up on that message, handling any questions it receives.

    2. cancellation_agent:
        The cancellation_agent is responsible for tour cancellations. It's job is to send slack notifications regarding a 
        specific tour cancellation to the correct slack channel.

    It is extremely important that you select the sub_agent that aligns most accurately with the given task.
    """,

    tools=[],
    sub_agents=[slack_agent, cancellation_agent]
)



