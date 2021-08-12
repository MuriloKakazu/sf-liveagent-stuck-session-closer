import os, json
from requests import Session
from salesforce import get_session_id


class LiveAgent(object):

    __CONNECTION = None
    __HOST = os.getenv('LIVEAGENT_HOST')
    __API_VERSION = os.getenv('LIVEAGENT_API_VERSION')
    __AFFINITY = None
    __SESSION_KEY = None
    __ORG_ID = os.getenv('SFDC_ORG_ID')
    __AGENT_ONLINE_STATUS = os.getenv('SFDC_AGENT_ONLINE_STATUS_ID')
    __TIMEOUT = 60
    __MESSAGES_POLL_COUNT = 0
    __MESSAGES_POLL_RETRIES = 0
    __MESSAGES_POLL_MAX_RETRIES = 3
    __SEQUENCE = 1


    def _create_connection(self):
        connection = Session()
        return connection

    def _get_connection(self):
        if not self.__CONNECTION:
            __CONNECTION = self._create_connection()
        return __CONNECTION

    def _get_base_headers(self):
        return {
            'X-LIVEAGENT-API-VERSION': self.__API_VERSION
        }

    def _append_auth_headers(self, headers):
        headers['X-LIVEAGENT-AFFINITY'] = self.__AFFINITY
        headers['X-LIVEAGENT-SESSION-KEY'] = self.__SESSION_KEY
        return headers

    def login_liveagent(self):
        headers = self._get_base_headers()
        headers['X-LIVEAGENT-AFFINITY'] = 'null' # because salesforce...
        
        response = self._get_connection().get(
            f'https://{self.__HOST}/chat/rest/System/SessionId?SessionId.ClientType=lightning',
            timeout=self.__TIMEOUT,
            headers=headers,
        )

        response.raise_for_status()

        session = json.loads(response.text)

        self.__AFFINITY = session['affinityToken']
        self.__SESSION_KEY = session['key']

    def login_omnichannel(self):
        headers = self._append_auth_headers(self._get_base_headers())
        headers['X-LIVEAGENT-SEQUENCE'] = str(self.__SEQUENCE)
        
        payload = {
            'organizationId': self.__ORG_ID,
            'sfdcSessionId': get_session_id(),
            'statusId': self.__AGENT_ONLINE_STATUS,
            'channelIdsWithParam': [
                {
                    'channelId': 'agent'
                },
                {
                    'channelId': 'conversational'
                },
                {
                    'channelId': 'lmagent'
                }
            ]
        }

        response = self._get_connection().post(
            f'https://{self.__HOST}/chat/rest/Presence/PresenceLogin',
            timeout=self.__TIMEOUT,
            headers=headers,
            data=json.dumps(payload)
        )
        response.raise_for_status()
        self.__SEQUENCE += 1

    def accept_work(self, agent_work_id, work_item_id):
        headers = self._append_auth_headers(self._get_base_headers())
        headers['X-LIVEAGENT-SEQUENCE'] = str(self.__SEQUENCE)

        payload = {
            'workId': agent_work_id,
            'workTargetId': work_item_id
        }

        response = self._get_connection().post(
            f'https://{self.__HOST}/chat/rest/Presence/AcceptWork',
            timeout=self.__TIMEOUT,
            headers=headers,
            data=json.dumps(payload)
        )
        response.raise_for_status()
        self.__SEQUENCE += 1


    def end_conversation(self, channel_type, work_item_id):
        headers = self._append_auth_headers(self._get_base_headers())
        headers['X-LIVEAGENT-SEQUENCE'] = str(self.__SEQUENCE)

        payload = {
            "channelType": channel_type,
            "workId": work_item_id
        }

        response = self._get_connection().post(
            f'https://{self.__HOST}/chat/rest/Conversational/ConversationEnd',
            timeout=self.__TIMEOUT,
            headers=headers,
            data=json.dumps(payload)
        )
        response.raise_for_status()
        self.__SEQUENCE += 1

    def close_work(self, agent_work_id, work_item_id):
        headers = self._append_auth_headers(self._get_base_headers())
        headers['X-LIVEAGENT-SEQUENCE'] = str(self.__SEQUENCE)

        payload = {
            'workId': agent_work_id,
            'workTargetId': work_item_id,
            'activeTime': 10
        }

        response = self._get_connection().post(
            f'https://{self.__HOST}/chat/rest/Presence/CloseWork',
            timeout=self.__TIMEOUT,
            headers=headers,
            data=json.dumps(payload)
        )
        response.raise_for_status()
        self.__SEQUENCE += 1

    def logout_liveagent(self):
        headers = self._append_auth_headers(self._get_base_headers())
        headers['X-LIVEAGENT-SEQUENCE'] = str(self.__SEQUENCE)

        response = self._get_connection().post(
            f'https://{self.__HOST}/chat/rest/Presence/PresenceLogout',
            timeout=self.__TIMEOUT,
            headers=headers,
            data={}
        )
        response.raise_for_status()
        self.__SEQUENCE += 1

    def delete_liveagent_session_id(self):
        headers = self._append_auth_headers(self._get_base_headers())

        response = self._get_connection().delete(
            f'https://{self.__HOST}/chat/rest/System/SessionId/{self.__SESSION_KEY}',
            timeout=self.__TIMEOUT,
            headers=headers
        )
        response.raise_for_status()

    # sequences:
    # -1 = Presence/PresenceConfiguration
    #  0 = Agent/LoginResult
    #  1 = AsyncResult ???
    #  2 = Presence/PresenceStatusChanged
    #  3 = Presence/PresenceStatusChanged
    #  4 = Presence/WorkAssigned
    #  5 = LmAgent/ChatRequest
    #  6 = Presence/WorkAccepted OR Presence/WorkRejected
    #  7 = AsyncResult ???
    #  8 = LmAgent/ChatEstablished
    #  9 = AsyncResult ???
    # 10 = Presence/AfterConversationWorkEnded
    # 11 = Presence/PresenceLogout
    def get_messages(self, sequence):
        headers = self._append_auth_headers(self._get_base_headers())

        response = self._get_connection().get(
            f'https://{self.__HOST}/chat/rest/System/Messages?ack={sequence}&pc={self.__MESSAGES_POLL_COUNT}',
            timeout=self.__TIMEOUT,
            headers=headers
        )
        self.__MESSAGES_POLL_COUNT += 1

        if response.status_code >= 300:
            print(response.content)

        response.raise_for_status()

        if response.status_code != 200:

            if self.__MESSAGES_POLL_RETRIES > self.__MESSAGES_POLL_MAX_RETRIES:
                raise Exception(f'Could not ACK sequence {sequence} after {self.__MESSAGES_POLL_MAX_RETRIES} retries. Aborting...')

            print(f'Could not ACK sequence {sequence}. Retrying... (retry count: {self.__MESSAGES_POLL_RETRIES})')
            self.__MESSAGES_POLL_RETRIES += 1
            return self.get_messages(sequence)

        self.__MESSAGES_POLL_RETRIES = 0
        return json.loads(response.text)