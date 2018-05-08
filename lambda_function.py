"""
This sample demonstrates a simple skill built with the Amazon Alexa Skills Kit.
The Intent Schema, Custom Slots, and Sample Utterances for this skill, as well
as testing instructions are located at http://amzn.to/1LzFrj6
For additional samples, visit the Alexa Skills Kit Getting Started guide at
http://amzn.to/1LGWsLG
"""

from __future__ import print_function

from utils.query_api import search_yelp
import logging


# --------------- Helpers that build all of the responses ----------------------

def build_speechlet_response(title, output, reprompt_text, should_end_session):
    return {
        'outputSpeech': {
            'type': 'PlainText',
            'text': output
        },
        'card': {
            'type': 'Simple',
            'title': "SessionSpeechlet - " + title,
            'content': "SessionSpeechlet - " + output
        },
        'reprompt': {
            'outputSpeech': {
                'type': 'PlainText',
                'text': reprompt_text
            }
        },
        'shouldEndSession': should_end_session
    }


def build_response(session_attributes, speechlet_response):
    return {
        'version': '1.0',
        'sessionAttributes': session_attributes,
        'response': speechlet_response
    }


# --------------- Functions that control the skill's behavior ------------------

def get_welcome_response():
    """ If we wanted to initialize the session to have some attributes we could
    add those here
    """

    session_attributes = {}
    card_title = "Welcome"
    speech_output = "Welcome to Mos Eisley Cantina! Tell me what kind "\
    "of cuisine you are looking for."
    # If the user either does not reply to the welcome message or says something
    # that is not understood, they will be prompted again with this text.
    reprompt_text = "Welcome to Mos Eisley Cantina! Tell me what kind "\
    "of cuisine you are looking for."
    should_end_session = False
    return build_response(session_attributes, build_speechlet_response(
        card_title, speech_output, reprompt_text, should_end_session))


def handle_session_end_request():
    card_title = "Session Ended"
    speech_output = "Thank you for trying the Alexa Skills Kit sample. " \
                    "Have a nice day! "
    # Setting this to true ends the session and exits the skill.
    should_end_session = True
    return build_response({}, build_speechlet_response(
        card_title, speech_output, None, should_end_session))


def build_output(session_attributes, card_title, should_end_session):
    """
    Depending on the session_attributes to build the output response
    :param session_attributes:
    :param card_title:
    :param should_end_session:
    :return:
    """
    if 'restaurant' in session_attributes:
        speech_output = "How about " + session_attributes['restaurant'] + " "
    elif 'location' in session_attributes :
        speech_output = "I now know your location is " + \
                        session_attributes['location'] + \
                        ". Which cuisine would you like? You can tell me your favorite food."
    elif 'cuisine' in session_attributes:
        speech_output = "I now know your favorite cuisine is " + \
                        session_attributes['cuisine'] + \
                        ". Where would you like me to look? You can tell me the 5 digit zipcode."
    else:
        speech_output = "I'm not sure what your favorite cuisine is. " \
                        "Please try again."
    return build_response(session_attributes, build_speechlet_response(
        card_title, speech_output, speech_output, should_end_session))


def update_cuisine_attributes(session_attributes, cuisine):
    session_attributes['cuisine'] = cuisine
    return session_attributes


def update_location_attributes(session_attributes, location):
    session_attributes["location"] = location
    return session_attributes


def update_restaurant_attributes(session_attributes, restaurant):
    session_attributes["restaurant"] = restaurant
    return session_attributes


def get_cuisine(session):
    if session.get('attributes', {}) and "cuisine" in session.get('attributes', {}):
        cuisine = session['attributes']['cuisine']
        return cuisine
    else:
        return None


def get_location(session):
    if session.get('attributes', {}) and "location" in session.get('attributes', {}):
        location = session['attributes']['cuisine']
        return location
    else:
        return None


def set_cuisine(intent, session):
    """ Sets the cuisine in the session and prepares the speech to reply to the
    user.
    """

    card_title = intent['name']
    session_attributes = session['attributes']
    should_end_session = False
    cuisine = None
    if 'food' in intent['slots']:
        cuisine = intent['slots']['food']['value']
        session_attributes = update_cuisine_attributes(session_attributes, cuisine)

    # check cuisine is set or not
    location = get_location(session)
    print(location, cuisine)
    if location is not None and cuisine is not None:
        places = search_yelp(keyword=cuisine, location=location, limit=1)
        update_restaurant_attributes(session_attributes, places[0]['name'])

    return build_output(session_attributes, card_title, should_end_session)


def set_location(intent, session):
    """ Sets the location in the session and prepares the speech to reply to the
    user.
    """

    card_title = intent['name']
    session_attributes = session['attributes']
    should_end_session = False
    location = None
    print(intent)
    if 'zip' in intent['slots'] and 'value' in intent['slots']['zip']:
        location = intent['slots']['zip']['value']
    if 'location' in intent['slots']and 'value' in intent['slots']['location']:
        location = intent['slots']['location']['value']

    if location is not None:
        update_location_attributes(session_attributes, location)

        # check cuisine is set or not
        cuisine = get_cuisine(session)
        if cuisine is not None:
            places = search_yelp(keyword=cuisine, location=location, limit=1)
            update_restaurant_attributes(session_attributes, places[0]['name'])

    return build_output(session_attributes, card_title, should_end_session)


# --------------- Events ------------------
# intent handler register
# adding your intent handler function name to her when you want to add your new intent
intent_handler = {
    'RequestRecommendation': set_cuisine,
    'SetConstraint': set_location
}



def on_session_started(session_started_request, session):
    """ Called when the session starts """

    print("on_session_started requestId=" + session_started_request['requestId']
          + ", sessionId=" + session['sessionId'])


def on_launch(launch_request, session):
    """ Called when the user launches the skill without specifying what they
    want
    """

    print("on_launch requestId=" + launch_request['requestId'] +
          ", sessionId=" + session['sessionId'])
    # Dispatch to your skill's launch
    return get_welcome_response()


def on_session_ended(session_ended_request, session):
    """ Called when the user ends the session.
    Is not called when the skill returns should_end_session=true
    """
    print("on_session_ended requestId=" + session_ended_request['requestId'] +
          ", sessionId=" + session['sessionId'])
    # add cleanup logic here


def state_manager(intent, session):
    """
    Add the state change logic here
    will add more logics here
    :param intent:
    :param session:
    :return:
    """
    if 'attributes' not in session:
        session['attributes'] = {}
    session['attributes']['state'] = intent['name']
    return intent_handler[intent['name']](intent, session)


def on_intent(intent_request, session):
    """ Called when the user specifies an intent for this skill """
    """ State Control Manager """

    print("on_intent requestId=" + intent_request['requestId'] +
          ", sessionId=" + session['sessionId'])

    intent = intent_request['intent']
    intent_name = intent_request['intent']['name']
    print(intent_name)
    # Dispatch to your skill's intent handlers
    if intent_name in intent_handler:
        # for the registered and our defined intent
        return state_manager(intent, session)
    elif intent_name == "AMAZON.HelpIntent":
        return get_welcome_response()
    elif intent_name == "AMAZON.CancelIntent" or intent_name == "AMAZON.StopIntent":
        return handle_session_end_request()
    else:
        raise ValueError("Invalid intent")





# --------------- Main handler ------------------

def lambda_handler(event, context):
    """ Route the incoming request based on type (LaunchRequest, IntentRequest,
    etc.) The JSON body of the request is provided in the event parameter.
    """
    print("event.session.application.applicationId=" +
          event['session']['application']['applicationId'])

    """
    Uncomment this if statement and populate with your skill's application ID to
    prevent someone else from configuring a skill that sends requests to this
    function.
    """
    # if (event['session']['application']['applicationId'] !=
    #         "amzn1.echo-sdk-ams.app.[unique-value-here]"):
    #     raise ValueError("Invalid Application ID")

    if event['session']['new']:
        on_session_started({'requestId': event['request']['requestId']},
                           event['session'])

    if event['request']['type'] == "LaunchRequest":
        return on_launch(event['request'], event['session'])
    elif event['request']['type'] == "IntentRequest":
        return on_intent(event['request'], event['session'])
    elif event['request']['type'] == "SessionEndedRequest":
        return on_session_ended(event['request'], event['session'])
    return logging.debug()