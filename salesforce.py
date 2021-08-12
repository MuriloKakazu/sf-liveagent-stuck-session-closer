import os
from simple_salesforce import Salesforce

__CONNECTION = None


def _create_connection():
    return Salesforce(
        client_id='Script',
        domain=os.getenv('SFDC_DOMAIN'),
        username=os.getenv('SFDC_USERNAME'),
        password=os.getenv('SFDC_PASSWORD'),
        security_token=os.getenv('SFDC_TOKEN'),
        version=os.getenv('SFDC_API_VERSION')
    )

def _get_connection():
    global __CONNECTION

    if not __CONNECTION:
        __CONNECTION = _create_connection()

    return __CONNECTION

def get_session_id():
    return _get_connection().session_id

def fetch_records(query):
    return _get_connection().query_all(query)['records']

def create_record(record_type, record):
    return _get_connection().__getattr__(record_type).create(record)

def update_record(record_type, record_id, record):
    return _get_connection().__getattr__(record_type).update(record_id, record)

def delete_record(record_type, record_id):
    return _get_connection().__getattr__(record_type).delete(record_id)