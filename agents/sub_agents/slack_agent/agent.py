from google.adk.agents.llm_agent import Agent
from agents.tools.slack_tools import reply_to_slack_message, send_slack_message, get_channel_id, update_tour_status, get_sheet_url
from google.adk.models.lite_llm import LiteLlm

slack_agent = Agent(
    model=LiteLlm(model="claude-sonnet-4-6"),
    name='slack_agent',
    description= """sends slack tour message and updates the specified tour's status in 
    the django database""",

    instruction = """

    As the slack_agent your responsibility is to handle the tour's that you are given with three
    main responsibilities. Always call all four of the first Tours tools in order for every new tour, regardless of
    previous interactions. Your second responsibility is to respond to general messages in the slack channels. For these messages you
    should use the fifth tool (reply_to_slack_messages).

    1. Obtain the slack channel id for the corresponding slack channel, given a tour's
    day of the week (Monday-Friday) and its time(9am - 4pm) that you extract from the query.
    You should use the tool "get_channel_id" to assist you and pass it the following arguments:
        week_day:str, time: int
    which you obtain from the prompt you received.

    2. Next obtain the URL for this tour's corresponding google sheets page. Sheet_url is obtained by making a call to the 
    get_sheet_url tool with the following arguments:
        week_number: int
    which you obtain from the prompt you recieved. If the call to get_sheet_url fails, return a default value of "0" for week_number
        
    3. Send out the proper message to the corresponding slack channel using the id that you
    previously obtained. The message is sent using the "send_slack_message" tool, and you should pass
    that tool the following arguments:
        channel_id:str, week_day: str, week_number: int, sheet_url: str, major_of_interest: str, contact_name: str, cell_number: str 
    which you obtain from the prompt you recieved and step 2 (sheet_url (or 0 if call fails). Note that major_of_interest might be either empty
    or misspelled, please pass the correct capitalzed spelling version of the major of interest. If major_of_interest, contact_name, or cell_number are empty/None
    then pass in empty strings to the send_slack_message tool.
    Make sure you send a message to the channel regardless, if you dont have any of the information just send a message without that specific information. 

    4. After sending the slack message, update the status of the specified tour in the django database.
    Use the tool "update_tour_status" to do this, and this tool the following arguments:
        event_id: str, status: str
    which you obtain from the prompt you received. If after step 3 the status includes "skipped", call 
    update_tour_status with "unassigned". The update status should reflect whether the slack message
    was sent successfuly. If the message was sent, then update status to "message_sent", otherwise update/keep
    the status to "unassigned"

    5. (FOR GENERAL REPLIES ONLY) To reply to general messages in slack, you should receive the channel id from the promopt, and use that channel
    id in your call to reply_to_slack_message in order to send a message in that channel. Please respond to each message in a professional tone, 
    as the goal is still to coordinate tours. 
    """,


    tools=[send_slack_message, get_channel_id, update_tour_status, get_sheet_url, reply_to_slack_message],
)