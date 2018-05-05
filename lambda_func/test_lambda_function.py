"""
This is our skeleton lambda function for testing interaction model
"""

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


def create_favorite_cuisine_attributes(favorite_cuisine):
    return {"favorite_Cuisine": favorite_cuisine}


def set_constraint(intent, session):
    """ Sets the cuisine in the session and prepares the speech to reply to the
    user.
    """

    card_title = intent['name']
    session_attributes = {}
    should_end_session = False

    if 'SetConstraint' in intent['slots']:
        if 'food' in intent['slots']['SetConstraint']:
            favorite_cuisine = intent['slots']['SetConstraint']['food']['value']
            session_attributes = create_favorite_cuisine_attributes(favorite_cuisine)
            speech_output = "I now know your favorite cuisine is " + \
                        favorite_cuisine + \
                        ". Where would you like me to look? You can tell me the 5 digit zipcode."
            reprompt_text = "Where would you like me to look? You can tell me the 5 digit zipcode."
        elif 'zip' in intent['slots']['SetConstraint']:
            loc_zip = intent['slots']['SetConstraint']['zip']['value']
            cuisine = get_cuisine(intent, session)
            session_attributes.update(create_location_attributes(loc_zip))
            speech_output = "I now know your location is " + loc_zip + " and your favorite food is " + cuisine + ". We will offer you recommendation later"
            reprompt_text = "I now know your location"
        else:
            speech_output = "I'm confused about something. Good luck darling!"
            reprompt_text = "I'm not sure what constraint you're trying to set. You can try again if you have the patience."
    else:
        speech_output = "I'm not sure what your favorite cuisine is. " \
                        "Please try again."
        reprompt_text = "I'm not sure what your favorite cuisine is. " 
    return build_response(session_attributes, build_speechlet_response(
        card_title, speech_output, reprompt_text, should_end_session))

def create_location_attributes(location):
    return {"location": location}

#def set_location(intent, session):
    """ Sets the location in the session and prepares the speech to reply to the
    user.
    """

#    card_title = intent['name']
#    session_attributes = session['attributes']
#    should_end_session = False
#
#    if 'Location' in intent['slots']:
#        location = intent['slots']['Location']['value']
#        cuisine = get_cuisine(intent, session)
#        session_attributes.update(create_location_attributes(location))
#        speech_output = "I now know your location is " + location + " and your favorite food is " + cuisine + ". We will offer you recommendation later"
#        reprompt_text = "I now know your location"
#    else:
#        speech_output = "I'm not sure what your favorite cuisine is. " \
#                        "Please try again."
#        reprompt_text = "I'm not sure what your favorite cuisine is. "
#    return build_response(session_attributes, build_speechlet_response(
#        card_title, speech_output, reprompt_text, should_end_session))


def get_cuisine(intent, session):
    session_attributes = {}
    reprompt_text = None

    if session.get('attributes', {}) and "favorite_Cuisine" in session.get('attributes', {}):
        favorite_Cuisine = session['attributes']['favorite_Cuisine']
        return favorite_Cuisine


def get_cuisine_from_session(intent, session):
    session_attributes = {}
    reprompt_text = None

    if session.get('attributes', {}) and "favorite_Cuisine" in session.get('attributes', {}):
        favorite_Cuisine = session['attributes']['favorite_Cuisine']
        speech_output = "Your favorite color is " + favorite_color + \
                        ". Goodbye."
        should_end_session = True
    else:
        speech_output = "I'm not sure what your favorite color is. " \
                        "You can say, my favorite color is red."
        should_end_session = False

    # Setting reprompt_text to None signifies that we do not want to reprompt
    # the user. If the user does not respond or says something that is not
    # understood, the session will end.
    return build_response(session_attributes, build_speechlet_response(
        intent['name'], speech_output, reprompt_text, should_end_session))


# --------------- Events ------------------

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


def on_intent(intent_request, session):
    """ Called when the user specifies an intent for this skill """

    print("on_intent requestId=" + intent_request['requestId'] +
          ", sessionId=" + session['sessionId'])

    intent = intent_request['intent']
    intent_name = intent_request['intent']['name']

    # Dispatch to your skill's intent handlers
    if intent_name == "SetConstraint":
        return set_constraint(intent, session)
    elif intent_name == "AMAZON.HelpIntent":
        return get_welcome_response()
    elif intent_name == "AMAZON.CancelIntent" or intent_name == "AMAZON.StopIntent":
        return handle_session_end_request()
    else:
        raise ValueError("Invalid intent")


def on_session_ended(session_ended_request, session):
    """ Called when the user ends the session.

    Is not called when the skill returns should_end_session=true
    """
    print("on_session_ended requestId=" + session_ended_request['requestId'] +
          ", sessionId=" + session['sessionId'])
    # add cleanup logic here


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
