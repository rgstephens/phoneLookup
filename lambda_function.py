"""
This sample demonstrates an implementation of the Lex Code Hook Interface
in order to serve a sample bot which manages reservations for hotel rooms and car rentals.
Bot, Intent, and Slot models which are compatible with this sample can be found in the Lex Console
as part of the 'BookTrip' template.

For instructions on how to set up and test this bot, as well as additional samples,
visit the Lex Getting Started documentation http://docs.aws.amazon.com/lex/latest/dg/getting-started.html.
"""

import json
import datetime
import time
import os
import logging
import requests
import paho.mqtt.publish as mqtt_publish
from pynamodb.models import Model
from pynamodb.attributes import UnicodeAttribute

logger = logging.getLogger()
logger.setLevel(logging.DEBUG)

class SessionModel(Model):
    """
    A DynamoDB User
    """
    class Meta:
        table_name = "ris-sessions"
        # host = "http://localhost:8000"
    session_id = UnicodeAttribute(hash_key=True)
    phone_number = UnicodeAttribute(range_key=True)
    # last_call = UnicodeAttribute(null=True)

# Create the table
if not SessionModel.exists():
    logger.warning("Creating dynamodb table")
    SessionModel.create_table(wait=True, read_capacity_units=1, write_capacity_units=1)

def safe_get(dct, *keys):
    for key in keys:
        try:
            dct = dct[key]
        except Exception:
            return None
    return dct


def confirm_intent(session_attributes, intent_name, slots, message):
    return {
        'sessionAttributes': session_attributes,
        'dialogAction': {
            'type': 'ConfirmIntent',
            'intentName': intent_name,
            'slots': slots,
            'message': message
        }
    }


def elicit_intent(session_attributes, message):
    logger.debug(f"ElicitIntent, Message: ${message}, session_attributes: {session_attributes}")
    response = {
        'sessionAttributes': session_attributes,
        'dialogAction': {
            'type': 'ElicitIntent',
            'message': message
        }
    }
    return response


def close(session_attributes, fulfillment_state, message):
    logger.debug(f"Close, Message: ${message}")
    response = {
        "sessionAttributes": session_attributes,
        "dialogAction": {
            "type": "Close",
            "fulfillmentState": fulfillment_state,
            "message": message,
        },
    }
    return response


def send_mqtt_utterance(sender_id, utterance):
    payload = f"{{\"sender_id\": \"{sender_id}\",\"utterance\":\"{utterance}\"}}"
    if 'MQTT_HOST' in os.environ and 'MQTT_USER' in os.environ and 'MQTT_PASS' in os.environ:
        mqtt_publish.single("rasa/lex/utterance", payload, hostname=os.environ['MQTT_HOST'], port=1883, client_id="lambdaRasa", auth = {'username': os.environ['MQTT_USER'], 'password': os.environ['MQTT_PASS']})


def send_mqtt_response(sender_id, response):
    payload = f"{{\"sender_id\": \"{sender_id}\",\"response\":\"{response}\"}}"
    if 'MQTT_HOST' in os.environ and 'MQTT_USER' in os.environ and 'MQTT_PASS' in os.environ:
        mqtt_publish.single("rasa/lex/response", payload, hostname=os.environ['MQTT_HOST'], port=1883, client_id="lambdaRasa", auth = {'username': os.environ['MQTT_USER'], 'password': os.environ['MQTT_PASS']})


def send_mqtt(sender_id, input_transcript, response):
    payload = f"{{\"sender_id\": \"{sender_id}\",\"utterance\":\"{input_transcript}\",\"response\":\"{response}\"}}"
    if 'MQTT_HOST' in os.environ and 'MQTT_USER' in os.environ and 'MQTT_PASS' in os.environ:
        mqtt_publish.single("rasa/lex/utterance", payload, hostname=os.environ['MQTT_HOST'], port=1883, client_id="lambdaRasa", auth = {'username': os.environ['MQTT_USER'], 'password': os.environ['MQTT_PASS']})

# --- Intents ---


def dispatch(intent_request):
    """
    Called when the user specifies an intent for this bot.
    """
    # logger.debug(f"dispatch, intent_request: {intent_request}")
    # session_attributes = intent_request['sessionAttributes'] if intent_request['sessionAttributes'] is not None else {}
    # lex v2
    # session_attributes = safe_get(intent_request, "sessionState", "sessionAttributes")
    # lex v1
    session_attributes = safe_get(intent_request, "sessionAttributes")
    logger.debug(f"session_attributes: {session_attributes}")
    session_id = safe_get(session_attributes, "ContactId")
    # Rasa sender_id will be set to the Amazon Connect PhoneNumber, otherwise the ContactId, otherwise ContactId
    if safe_get(session_attributes, "PhoneNumber"):
        # PhoneNumber could be empty
        sender_id = session_attributes.get("PhoneNumber", session_attributes.get("ContactId", 'lex'))
    # Determine if this is a new chat session
    try:
        # Lookup session_id in Dynamo
        logger.debug(f"Lookup session_id: {session_id}")
        session_exists = SessionModel.get(session_id, sender_id)
    except:
        session_exists = False
    logger.debug(f"session_exists for {session_id}: {session_exists}, sender_id: {sender_id}")
    if not session_exists:
        logger.info(f"New session for {sender_id}")
        session = SessionModel(session_id, sender_id)
        session.save()
    logger.debug(f"session_attributes: {session_attributes}")
    rasa_host = os.environ.get("RASA_HOST")
    url = f"http://{rasa_host}/webhooks/rest/webhook"
    logger.debug(f"RASA_HOST: {rasa_host}, url: {url}")
    input_transcript = intent_request.get("inputTranscript", "")
    logger.debug(f"input_transcript: {input_transcript}")
    if not input_transcript:
        logger.debug("empty input transcript, sending /greet")
        input_transcript = "/greet"

    # Check if the user said nothing and prompt
    if not input_transcript:
        return elicit_intent(
            session_attributes,
            {
                'contentType': 'PlainText',
                'content': 'How can I help you?'
            }
        )
    elif rasa_host:
        payload = json.dumps({"sender": sender_id, "message": input_transcript, "metadata": session_attributes})
        headers = {"Content-Type": "application/json"}
        # https://realpython.com/python-requests/
        response = requests.post(url, headers=headers, data=payload)
        r = response.json()
        logger.debug(f"r: {r}")
        if response.status_code == 200:
            logger.debug(f"response status_code: {response.status_code}, r: {r}, type(r): {type(r)}")
            if len(r) > 0:
                send_mqtt_utterance(sender_id, input_transcript)
                logger.debug(f"len(r): {len(r)}")
                message = ""
                for resp in r:
                    logger.debug(f"resp: {resp}, type(resp): {type(resp)}")
                    message += safe_get(resp, 'text') + "\n"
                send_mqtt_response(sender_id, message)
                return elicit_intent(
                    session_attributes,
                    {
                        'contentType': 'PlainText',
                        'content': message
                    }
                )
            else:
                return close(
                    session_attributes,
                    'Fulfilled',
                    {
                        'contentType': 'PlainText',
                        'content': 'The scheduling service is currently down'
                    }
                )

        else:
            text = "Error: Sorry, bot is not responding. Try again another time."
            send_mqtt(sender_id, input_transcript, f"Error: Bot not responding {response.status_code}")
            return close(
                session_attributes,
                'Fulfilled',
                {
                    'contentType': 'PlainText',
                    'content': text
                }
            )
    else:
        msg = "Error: RASA_HOST or input_transcript not set"
        send_mqtt(sender_id, input_transcript, msg)
        logger.debug(f"Calling close: {msg}")
        return close(
            session_attributes,
            'Fulfilled',
            {
                'contentType': 'PlainText',
                'content': msg
            }
        )

    logger.debug(f"exit, calling close")
    return close(
        session_attributes,
        "Fulfilled",
        {"contentType": "PlainText", "content": "Rasa says Hi!"},
    )

    # raise Exception('Intent with name ' + intent_name + ' not supported')


def lambda_handler(event, context):
    """
    Route the incoming request based on intent.
    The JSON body of the request is provided in the event slot.
    """
    # By default, treat the user request as coming from the America/New_York time zone.
    os.environ["TZ"] = "America/Los_Angeles"
    time.tzset()
    logger.debug(f"event: {event}")
    return dispatch(event)
