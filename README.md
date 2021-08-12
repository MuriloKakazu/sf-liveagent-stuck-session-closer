# Script to close Salesforce messaging sessions stuck for >24h.

These conversation sessions will get stuck if Salesforce f-s up when routing a customer conversation session to a queue or to an agent, resulting in the session becoming stuck in a Pending state, which essentially prevents the customer to be serviced ever again, or until the session is actually closed manually one by one on the MessagingSession list view interface. 

Since Salesforce does not close these sessions automatically nor we want to close these manually through the interface, and there's no way to update the MessagingSession's status field via Apex or the Rest API, I made this script to be able to close them by reverse-engineering the scripts and http requests made by the service agent's browser when logged into Omni-Channel and the LiveAgent API

## Before you run

### Install dependencies
- [Python 3.X](https://www.python.org/downloads/)
- [Pipenv](https://pipenv.pypa.io/en/latest/)

And also install project dependencies:
```
pipenv install
```

###

⚠️ Any variable that requires credentials of a user that has a Messaging license and is assigned to a queue that routes messaging sessions will be marked with this icon

### Config your .env file

| ENVIRONMENT VARIABLE          | DESCRIPTION                                                                 |
|-------------------------------|-----------------------------------------------------------------------------|
| `SFDC_DOMAIN`                 | `login` for prod or `test` for sandbox                                      |
| `SFDC_USERNAME`               | admin or integration user username ⚠️                                       |
| `SFDC_PASSWORD`               | admin or integration user password ⚠️                                       |
| `SFDC_TOKEN`                  | admin or integration user personal token ⚠️                                 |
| `SFDC_API_VERSION`            | `52.0` or later                                                             |
| `SFDC_ORG_ID`                 | organization id                                                             |
| `SFDC_AGENT_ONLINE_STATUS_ID` | id of an "available" ServicePresenceStatus                                  |
| `SFDC_AGENT_USER_ID`          | admin or integration user id ⚠️                                             |
| `SFDC_AGENT_CHANNEL_ID`       | id of ServiceChannel for messaging sessions                                 |
| `LIVEAGENT_HOST`              | host of the liveagent api e.g: `abcd.la4-c3-ph2.salesforceliveagent.com`    |
| `LIVEAGENT_API_VERSION`       | `52` or later                                                               |

## How to run

Create a shell in the virtual env:
```
pipenv shell
```

Then run:
```
python3 run.py
```
