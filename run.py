import os, time, datetime
from dotenv import load_dotenv
from salesforce import delete_record, fetch_records, create_record, update_record
from liveagent import LiveAgent


load_dotenv()


def get_message(messages, type):
    for message in messages['messages']:
        if message['type'] == type:
            return message['message']
    return None


stuck_conversations_query = """
select      id 
from        messagingsession 
where       status in ('New', 'Waiting', 'Active') 
and         starttime < yesterday
order by    starttime
"""

stuck_conversations = fetch_records(stuck_conversations_query)

liveagent = LiveAgent()

liveagent.login_liveagent()
print('logged in LiveAgent')

liveagent.login_omnichannel()
print('logged in Omni-Channel')

for conversation in stuck_conversations:
    print(f'processing conversation: {conversation["Id"]}')

    update_record('MessagingSession', conversation['Id'], {'OwnerId': os.getenv('SFDC_AGENT_USER_ID')})

    pending_routing = fetch_records(f"select id from pendingservicerouting where workitemid = '{conversation['Id']}'")
    if pending_routing:
        delete_record('PendingServiceRouting', pending_routing[0]['Id'])
        print('found and deleted a PendingServiceRouting related to this conversation, otherwise the script would not be able to process it ;)')

    agent_work_result = create_record('AgentWork', {
        'WorkItemId': conversation['Id'],
        'UserId': os.getenv('SFDC_AGENT_USER_ID'),
        'OwnerId': os.getenv('SFDC_AGENT_USER_ID'),
        'ServiceChannelId': os.getenv('SFDC_AGENT_CHANNEL_ID')
    });
    if not agent_work_result['success']:
        raise Exception(f'Could not create AgentWork: {agent_work_result}')
    print(f'created AgentWork {agent_work_result["id"]}')

    messages = liveagent.get_messages(-1)
    next_sequence = messages['sequence']

    work_assigned_message = get_message(messages, 'Presence/WorkAssigned')
    if not work_assigned_message:
        raise Exception('expected Presence/WorkAssigned message not found')

    agent_work_id = work_assigned_message['workId']
    work_item_id = work_assigned_message['workTargetId']
    print(f'found AgentWork {agent_work_id} and WorkItem {work_item_id}')

    liveagent.accept_work(agent_work_id, work_item_id)
    print('accepted AgentWork')

    messages = liveagent.get_messages(next_sequence)
    next_sequence = messages['sequence']

    liveagent.end_conversation('lmagent', work_item_id)
    print('ended conversation')

    liveagent.close_work(agent_work_id, work_item_id)
    print('closed work')

    # messages = liveagent.get_messages(next_sequence)
    # next_sequence = messages['sequence']
    # print(messages)

    print(f'conversation finished processing: {conversation["Id"]}')
    print('----')

# liveagent.logout_liveagent()
# print('logged out LiveAgent')
liveagent.delete_liveagent_session_id()
print('deleted LiveAgent sessionId')