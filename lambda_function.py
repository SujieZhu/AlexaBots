"""
TODO: add description
"""

from utils.query_api import *
import logging
import random
import boto3
from boto3.dynamodb.conditions import Key, Attr

from dynamo_db.dynamo import make_user_info_item, get_item_by_key

# --------------- Load DynamoDB settings ----------------------

dynamodb = boto3.resource('dynamodb')
user_info = dynamodb.Table('UserInfo')
previous_recs = dynamodb.Table('PreviousRecommendations')

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
    speech_output = "Welcome back to Mos Eisley Cantina! Tell me what kind " \
                    "of cuisine you are looking for."
    # If the user either does not reply to the welcome message or says something
    # that is not understood, they will be prompted again with this text.
    reprompt_text = "Welcome to Mos Eisley Cantina! Tell me what kind " \
                    "of cuisine you are looking for."
    should_end_session = False
    return build_response(session_attributes, build_speechlet_response(
        card_title, speech_output, reprompt_text, should_end_session))


def prompt_for_defaults():
    """prompt user for default settings"""
    session_attributes = {}
    card_title = "Welcome"
    speech_output = "Welcome to Mos Eisley Cantina. Looks like you're new. Let's set some default " \
                    "locations for looking up restaurants in future. You can set home and or " \
                    "work, by address, zip, or both."
    reprompt_text = "Sorry I didn't get that. Say: home address, work address," \
                    "home zip, or work zip."
    should_end_session = False
    return build_response(session_attributes, build_speechlet_response(
        card_title, speech_output, reprompt_text, should_end_session))


def handle_session_end_request():
    card_title = "Session Ended"
    speech_output = "Thank you for trying the Mos Eisley cantina. " \
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
    print(session_attributes)
    if 'SetConstraint' == session_attributes['state']:
        lack = check_constraints(session_attributes)
        # check info is sufficient or not
        if len(lack) == 0:
            # if constraints is sufficient, provide restaurant
            return offer_recommendation(session_attributes, card_title, should_end_session)
        else:
            # if not sufficient, ask user to provide other info
            return prompt_constraint(session_attributes, lack, card_title, should_end_session)

    if 'ChangeRecommendation' == session_attributes['state']:
        return offer_recommendation(session_attributes, card_title, should_end_session)      

    if 'restaurant' in session_attributes:
        speech_output = "How about " + session_attributes['restaurant'] + " "
    return build_response(session_attributes, build_speechlet_response(
        card_title, speech_output, speech_output, should_end_session))


def prompt_constraint(session_attributes, lack, card_title, should_end_session):
    """
    randomly pick one un-provided constraint to the user
    TODO: Add more random response sentence
    :param session_attributes:
    :param lack:
    :param card_title:
    :param should_end_session:
    :return:
    """
    reprompt = {
        'location': "Where would you like me to look? You can tell me the 5 digit zipcode or your address.",
        'food': "Which cuisine would you like? You can tell me your favorite food."
    }

    key = random.randint(0, len(lack)-1)
    speech_output = reprompt[lack[key]]
    return build_response(session_attributes, build_speechlet_response(
        card_title, speech_output, speech_output, should_end_session))


def offer_recommendation(session_attributes, card_title, should_end_session):
    """
    The output speech for offer restaurants
    TODO: Add more random response with restaurant name
    :param session_attributes:
    :param card_title:
    :param should_end_session:
    :return:
    """
    name = session_attributes['restaurant']['name']
    rating = session_attributes['restaurant']['rating']
    review_count = session_attributes['restaurant']['review_count']
    price = session_attributes['restaurant']['price']
    speech_output = "How about {}? They have {} reviews and their rating is {}. \
    Do you need more infomation about this place ?".format(name, review_count, rating)
    # TODO: if a place is too expensive, recommende other cheaper place
    if price > 3:
        speech_output = speech_output + " But the price there is pretty expensive. Do you need me to find a cheaper one?"
    return build_response(session_attributes, build_speechlet_response(
        card_title, speech_output, speech_output, should_end_session))
    

def offer_more_data(session_attributes, card_title, should_end_session, infotype):
    """
    The output speech for offer more data
    TODO: support more infotype
    :param session_attributes:
    :param card_title:
    :param should_end_session:
    :return:
    """

    # id for business detail
    _id = session_attributes['restaurant']['id']
    place = search_yelp_business(_id)

    if infotype == 'phone number':
        phone = place['display_phone']
        speech_output = "Their phone number is {}.".format(phone)
    elif infotype == 'address':
        address = place['location']['display_address']
        speech_output = "Their address is {} {}.".format(address[0], address[1])
    return build_response(session_attributes, build_speechlet_response(
        card_title, speech_output, speech_output, should_end_session))



def check_constraints(session_attributes):
    """
    check the constraints' sufficiency to call yelp API
    if the constraints is sufficiency, call yelp to generate the restaurant
    if not sufficient, produce the constraints list for the output
    :param session_attributes:
    :return:
    """
    lack = []
    parameters = {}
    for key in require_constraints:
        if key in session_attributes:
            parameters[key] = session_attributes[key]
        else:
            lack.append(key)
    if len(lack) == 0:
        search_with_parameter(session_attributes)
    return lack


def search_with_parameter(session_attributes, rank = 0):
    """
    call the Yelp API with the parameter dict
    TODO: add more parameter mapping to call YELP API(add more search constraints)
    TODO: not hard-coded
    :param session_attributes:
    :param parameters: parameter dict
    :return:
    """
    cuisine = session_attributes['food']
    location = session_attributes['location']
    places = search_yelp(keyword=cuisine, location=location, limit=rank+1)
    name = places[len(places)-1]['name']
    print(name)
    update_restaurant_attributes(session_attributes, places[len(places) - 1])
    update_rank_attributes(session_attributes, rank)


def update_cuisine_attributes(session_attributes, cuisine):
    session_attributes['food'] = cuisine
    return session_attributes


def update_rank_attributes(session_attributes, rank):
    session_attributes['rank'] = rank
    return session_attributes


def update_location_attributes(session_attributes, location):
    session_attributes["location"] = location
    return session_attributes


def update_restaurant_attributes(session_attributes, restaurant):
    session_attributes['restaurant'] = {}
    session_attributes['restaurant']['name'] = restaurant['name']
    session_attributes['restaurant']['rating'] = restaurant['rating']
    session_attributes['restaurant']['review_count'] = restaurant['review_count']
    session_attributes['restaurant']['price'] = len(restaurant['price'])
    session_attributes['restaurant']['id'] = restaurant['id']
    return session_attributes


def get_cuisine(session):
    if session.get('attributes', {}) and "food" in session.get('attributes', {}):
        cuisine = session['attributes']['food']
        return cuisine
    else:
        return None


def get_location(session):
    if session.get('attributes', {}) and "location" in session.get('attributes', {}):
        location = session['attributes']['location']
        return location
    else:
        return None


def get_value_from_intent(intent, name):
    if name in intent['slots'] and 'value' in intent['slots'][name]:
        return intent['slots'][name]['value']
    else:
        return None


def update_session_attribute(session_attributes, key, value):
    """
    Update one attribute of session
    Can check the None value
    :param session_attributes:
    :param key:
    :param value:
    :return:
    """
    if value is None:
        return
    else:
        if key == 'zip':
            key = 'location'
        session_attributes[key] = value
        return


def set_constraint(intent, session):
    """
    Set the constraints of the search
    :param intent:
    :param session:
    :return:
    """
    card_title = intent['name']
    session_attributes = session['attributes']
    should_end_session = False

    for key in constraints:
        value = get_value_from_intent(intent, key)
        update_session_attribute(session_attributes, key, value)

    return build_output(session_attributes, card_title, should_end_session)


def request_data(intent, session):
    """
    request data by the user
    TODO: add request data from the new Yelp api
    :param intent:
    :param session:
    :return:
    """
    card_title = intent['name']
    session_attributes = session['attributes']
    should_end_session = False
    infotype = get_value_from_intent(intent, 'infotype')
    return offer_more_data(session_attributes, card_title, should_end_session, infotype)


def change_recommendation(intent, session):
    """
    change recommendation by the user
    TODO: relative index instead of the random one
    TODO: how to provide a list of restaurant for the user to choose? so that user could say fifth one?
    :param intent:
    :param session:
    :return:
    """
    card_title = intent['name']
    session_attributes = session['attributes']
    should_end_session = False

    rank = session_attributes['rank']
    if 'next' in intent['slots'] and 'value' in intent['slots']['next']:
        rank = rank + 1
    if 'sequence' in intent['slots'] and 'value' in intent['slots']['sequence']:
        if intent['slots']['sequence']['value'] == 'previous' and rank > 0:
            rank = rank - 1
        else:
            # now only support the next and previous one
            rank = rank + 1

    # search with the new rank, it will update the restaurant name and the rank number
    search_with_parameter(session_attributes, rank)

    return build_output(session_attributes, card_title, should_end_session)


def change_constraint(intent, session):
    """
    chaneg constraint by the user
    TODO: change constraints
    :param intent:
    :param session:
    :return:
    """
    card_title = intent['name']
    session_attributes = session['attributes']
    should_end_session = False
    return


def unsolved_output(intent, session):
    """
    For unsolved state or input, prompt all the current attributes
    TODO: add more reprompt according to the previous state info
    :param intent:
    :param session:
    :return:
    """
    card_title = intent['name']
    session_attributes = session['attributes']
    should_end_session = False
    speech_output = ""
    if 'location' in session_attributes:
        speech_output += "I now know your location is " + \
                        session_attributes['location'] + ". "
    if 'cuisine' in session_attributes:
        speech_output += "I now know your favorite cuisine is " + \
                        session_attributes['cuisine'] + ". "
    else:
        speech_output = "I'm not sure what your favorite cuisine is. " \
                        "Please try again."
    return build_response(session_attributes, build_speechlet_response(
        card_title, speech_output, speech_output, should_end_session))


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
        update_restaurant_attributes(session_attributes, places[0])

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
            update_restaurant_attributes(session_attributes, places[0])

    return build_output(session_attributes, card_title, should_end_session)



# --------------- Events ------------------
# intent handler register
# adding your intent handler function name to her when you want to add your new intent
intent_handler = {
    'SetConstraint': set_constraint,
    'RequestMoreData': request_data,
    'ChangeRecommendation': change_recommendation,
    'ChangeConstraint': change_constraint,
    'Unsolved': unsolved_output,
}

# global variables for the constraints
constraints = ['food', 'location', 'zip', 'now']
# global variables for the required constraints used in prompt_constraint function
# will add more in the future
require_constraints = ['food', 'location']


previous_state = {
    'SetConstraint': {'initial', 'SetConstraint'},
    'RequestMoreData': {'SetConstraint', 'ChangeRecommendation','RequestMoreData'},
    'ChangeRecommendation': {'SetConstraint', 'RequestMoreData', 'ChangeRecommendation'},
    'ChangeConstraint': {'SetConstraint', 'RequestMoreData', 'ChangeRecommendation', 'ChangeConstraint'},
}


def check_previous_state(session):
    """
    check the
    :param session:
    :return: boolean
    """
    previous = session['attributes']['previous_state']
    current = session['attributes']['state']
    if previous in previous_state[current]:
        return True
    else:
        return False


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
    # check whether first time user
    # if you want to pretend you're unrecognised for testing make 'this_user_id' into a bogus value like 'abcdef'
    this_user_id = session["user"]["userId"]
    if not get_item_by_key(user_info, 'user_id', this_user_id):
        # if you want to add thing to the DB do it this way:
        # user_info.put_item(Item=make_user_info_item(this_user_id)
        return prompt_for_defaults()
    else:
        # return get_welcome_back_response()
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
        session['attributes']['state'] = 'initial'
    session['attributes']['previous_state'] = session['attributes']['state']
    session['attributes']['state'] = intent['name']
    if check_previous_state(session):
        return intent_handler[intent['name']](intent, session)
    else:
        # not update the current state, roll back to the previous state
        session['attributes']['state'] = session['attributes']['previous_state']
        return intent_handler['Unsolved'](intent, session)


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
