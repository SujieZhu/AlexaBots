"""
TODO: add description
"""

from utils.query_api import *
import logging
import random
import time
import boto3
from boto3.dynamodb.conditions import Key, Attr

from dynamo_db.dynamo import *

# --------------- Load DynamoDB settings ----------------------

dynamodb = boto3.resource('dynamodb')
user_info = dynamodb.Table('UserInfo')
previous_recs = dynamodb.Table('PreviousRecommendations')

# Get time, and we can use this info to infer if the user want places which is open now.
time_array = time.localtime()  # return time of current time zone, sample return:
# time.struct_time(tm_year=2018, tm_mon=5, tm_mday=15, tm_hour=14, tm_min=53, tm_sec=20, tm_wday=1, tm_yday=135, tm_isdst=1)
tm_hour = time_array[3]
tm_min = time_array[4]
tm_wday = time_array[6]

current_place = '710 NE 42nd street, seattle, 98105'


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
                    "locations for looking up restaurants in the future. You can set home and" \
                    "work zip."
    reprompt_text = "Sorry I didn't get that. Say: home zip or work zip."

    should_end_session = False
    return build_response(session_attributes, build_speechlet_response(
        card_title, speech_output, reprompt_text, should_end_session))


def handle_session_end_request(session):
    # end the session and save the user info to the database
    card_title = "Session Ended"
    speech_output = "Thank you for trying the Mos Eisley cantina. We hope you enjoy your meal. " \
                    "Have a nice day! "
    # Setting this to true ends the session and exits the skill.
    should_end_session = True

    item = make_user_previous_recommendation_item(session)
    print('write to the dynamo db')
    print(item)
    print(previous_recs.put_item(Item=item))
    print('successfully write out')
    return build_response(session['attributes'], build_speechlet_response(
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

    if 'SetDefaults' == session_attributes['state']:
        which_zip = session_attributes['which_zip']
        # print('jeenkies! ', get_item_by_key(user_info, session_attributes['this_user_id'], session_attributes['which_zip'] ))
        speech_output = "Okay, {} zipcode set.".format(which_zip)

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

    key = random.randint(0, len(lack) - 1)
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
    speech_output = "How about {}? They have {} reviews and their rating is {}.".format(name, review_count, rating)

    # TODO: recommend a better way to get there.
    distance = session_attributes['restaurant']['walking_distance']
    walking_duration = session_attributes['restaurant']['walking_duration']
    driving_duration = session_attributes['restaurant']['driving_duration']
    speech_output = speech_output + " It is {} away and it take {} to walk there or {} to drive there.".format(distance,
                                                                                                               walking_duration,
                                                                                                               driving_duration)

    speech_output = speech_output + " Do you need more infomation about this place ?"
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

    # id for business detail, used for adding more detail info.
    _id = session_attributes['restaurant']['id']

    restaurant = session_attributes['restaurant']

    if infotype == 'phone number':
        phone = restaurant['display_phone']
        speech_output = "Their phone number is {}.".format(phone)
    elif infotype == 'address':
        address = restaurant['location']['display_address']
        speech_output = "Their address is {}.".format(address)
    elif infotype == 'opening hour':
        restaurant = search_yelp_business(_id)
        opening_hour = restaurant['hours'][0]['open'][tm_wday]['end']
        speech_output = "They open until {}:{} today.".format(opening_hour[0:2], opening_hour[2:4])
    # Just text excerpt, maybe not useful
    elif infotype == 'reviews':
        restaurant = search_yelp_business(_id + '/reviews')
        speech_output = restaurant['reviews'][0]['text']
    return build_response(session_attributes, build_speechlet_response(
        card_title, speech_output, speech_output, should_end_session))


def end_session(session_attributes, card_title, should_end_session=True):
    """
    The output speech for ending the session
    :param session_attributes:
    :param card_title:
    :param should_end_session:
    :return:
    """
    speech_output = 'Thank you for using our mos eisley cantina. We hope you enjoy your meal. Have a nice day.'
    item = make_user_previous_recommendation_item(session_attributes)
    print('write to the dynamo db')
    print(item)
    print(previous_recs.put_item(Item=item))
    return build_response(session_attributes, build_speechlet_response(
        card_title, speech_output, speech_output, should_end_session))


def check_constraints(session_attributes):
    """
    check the constraints' sufficiency to call yelp API
    if the constraints is sufficient, call yelp to generate the restaurant
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


def search_with_parameter(session_attributes, rank=0):
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
    places = search_yelp(keyword=cuisine, location=location, limit=rank + 1)
    name = places[len(places) - 1]['name']
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
    # TODO: dynamo db only support int
    session_attributes['restaurant']['rating'] = int(restaurant['rating'])
    session_attributes['restaurant']['review_count'] = restaurant['review_count']
    session_attributes['restaurant']['price'] = len(restaurant['price'])
    session_attributes['restaurant']['id'] = restaurant['id']
    session_attributes['restaurant']['display_phone'] = restaurant['display_phone']
    destination_place = restaurant['location']['display_address'][0] + restaurant['location']['display_address'][1]
    session_attributes['restaurant']['display_address'] = destination_place
    walking_direction = get_google_direction('walking', current_place, destination_place)
    session_attributes['restaurant']['walking_distance'] = walking_direction['distance']['text']
    session_attributes['restaurant']['walking_duration'] = walking_direction['duration']['text']
    driving_direction = get_google_direction('driving', current_place, destination_place)
    session_attributes['restaurant']['driving_distance'] = driving_direction['distance']['text']
    session_attributes['restaurant']['driving_duration'] = driving_direction['duration']['text']
    return session_attributes


def get_cuisine(session):
    if session.get('attributes', {}) and "food" in session.get('attributes', {}):
        cuisine = session['attributes']['food']
        return cuisine
        return None


def get_location(session):
    if session.get('attributes', {}) and "location" in session.get('attributes', {}):
        location = session['attributes']['location']
        return location
    return None


def get_value_from_intent(intent, name):
    if name in intent['slots'] and 'value' in intent['slots'][name]:
        return intent['slots'][name]['value']
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
    change constraint by the user
    TODO: change constraints
    :param intent:
    :param session:
    :return:
    """
    card_title = intent['name']
    session_attributes = session['attributes']
    should_end_session = False
    return


def is_positive_feedback(intent):
    """
    check whether is the positive feedback
    :param intent:
    :return:
    """
    if 'positive' in intent['slots'] and 'value' in intent['slots']['positive']:
        return True
    elif 'negative' in intent['slots'] and 'value' in intent['slots']['negative']:
        return False
    else:
        return None


def give_feedback(intent, session):
    """
    record user's feedback for restarting previous conversation or after recommendation
    TODO: change constraints
    :param intent:
    :param session:
    :return:
    """
    card_title = intent['name']
    session_attributes = session['attributes']
    should_end_session = False

    # ask feedback uses the dynamodb info to ask for user feedback of the previous
    if session_attributes['previous_state'] == 'AskFeedback':
        # positive feedback
        if is_positive_feedback(intent):
            # copy the previous session information
            session_attributes['food'] = session_attributes['user_history']['food']
            session_attributes['location'] = session_attributes['user_history']['location']
            session_attributes['rank'] = int(session_attributes['user_history']['rank'])
            rank = session_attributes['rank']
            session_attributes.pop('user_history')
            # search with the new rank, it will update the restaurant name and the rank number
            rank = rank + 1
            print('new search')
            print(session_attributes)
            print(rank)
            search_with_parameter(session_attributes, rank)
            # offer a new recommendation based on previous information
            return offer_recommendation(session_attributes, card_title, should_end_session)
        # negative feedback
        else:
            # ask user for the new food preference and information.
            # TODO: ask user what information to keep. change the recommendations
            session_attributes.pop('user_history')
            session_attributes['state'] = 'initial'
            lack = check_constraints(session_attributes)
            # ask user to provide other info
            return prompt_constraint(session_attributes, lack, card_title, should_end_session)
    # feedback about the recommendation
    else:
        # positive feedback
        if is_positive_feedback(intent):
            # user satisfies with the recommendation
            # end this session and save to dynamodb
            return handle_session_end_request(session)
        # negative feedback
        else:
            # user not satisfied with the recommendation, change another restaurant.
            rank = session_attributes['rank']
            # search with the new rank, it will update the restaurant name and the rank number
            rank = rank + 1
            print('new search')
            print(session_attributes)
            search_with_parameter(session_attributes, rank)
            # offer a new recommendation based on previous information
            return offer_recommendation(session_attributes, card_title, should_end_session)
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
    if 'location' in intent['slots'] and 'value' in intent['slots']['location']:
        location = intent['slots']['location']['value']

    if location is not None:
        update_location_attributes(session_attributes, location)

        # check cuisine is set or not
        cuisine = get_cuisine(session)
        if cuisine is not None:
            places = search_yelp(keyword=cuisine, location=location, limit=1)
            update_restaurant_attributes(session_attributes, places[0])

    return build_output(session_attributes, card_title, should_end_session)


def set_default_zips(intent, session):
    """
	Sets the users default work or home zipcode.
    """

    card_title = intent['name']
    session_attributes = session['attributes']
    should_end_session = False
    this_user_id = session["user"]["userId"]
    session_attributes['this_user_id'] = this_user_id

    if 'value' in intent['slots']['homezip']:
        new_home_zip = intent['slots']['homezip']['value']

        key_value = dict({'user_id':this_user_id})
        attUpdate_value = dict({'home_zip':{'Value':new_home_zip}})

        user_info.update_item(Key=key_value, AttributeUpdates=attUpdate_value )
        session_attributes['which_zip'] = 'home'

    if 'value' in intent['slots']['workzip']:
        new_work_zip = intent['slots']['workzip']['value']

        key_value = dict({'user_id': this_user_id})
        attUpdate_value = dict({'work_zip': {'Value':new_work_zip}})

        user_info.update_item(Key=key_value, AttributeUpdates=attUpdate_value)
        session_attributes['which_zip'] = 'home and work' if (session_attributes.get('which_zip') == 'home') else 'work'

    return build_output(session_attributes, card_title, should_end_session)


# --------------- Events ------------------
# intent handler register
# adding your intent handler function name to her when you want to add your new intent
intent_handler = {
    'SetConstraint': set_constraint,
    'RequestMoreData': request_data,
    'ChangeRecommendation': change_recommendation,
    'ChangeConstraint': change_constraint,
    'GiveFeedback': give_feedback,
    'Unsolved': unsolved_output,
    'SetDefaults': set_default_zips
}

# global variables for the constraints
constraints = ['food', 'location', 'zip', 'now']

# global variables for the required constraints used in prompt_constraint function
# will add more in the future
require_constraints = ['food', 'location']

previous_state = {
    'SetConstraint': {'initial', 'SetConstraint', 'SetDefaults'},
    'RequestMoreData': {'SetConstraint', 'ChangeRecommendation', 'RequestMoreData'},
    'ChangeRecommendation': {'SetConstraint', 'RequestMoreData', 'ChangeRecommendation'},
    'ChangeConstraint': {'SetConstraint', 'RequestMoreData', 'ChangeRecommendation', 'ChangeConstraint'},
    'GiveFeedback': {'SetDefaults', 'AskFeedback', 'SetConstraint', 'RequestMoreData', 'ChangeRecommendation', 'ChangeConstraint',
                     'GiveFeedback'},
    'SetDefaults': {'initial', 'SetDefaults'}
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
    return False


def on_session_started(session_started_request, session):
    """ Called when the session starts """

    print("on_session_started requestId=" + session_started_request['requestId']
          + ", sessionId=" + session['sessionId'])


def on_launch(launch_request, session):
    """ Called when the user launches the skill without specifying what they
    want

    two kinds of responses, randomly pick, ask user for feedback
    """

    print("on_launch requestId=" + launch_request['requestId'] +
          ", sessionId=" + session['sessionId'])
    # check whether first time user
    # if you want to pretend you're unrecognised for testing make 'this_user_id' into a bogus value like 'abcdef'
    this_user_id = session["user"]["userId"]
    user_history = get_item_by_key(previous_recs, 'user_id', this_user_id)
    print(user_history)
    if not user_history:
        # if you want to add thing to the DB do it this way:
        # user_info.put_item(Item=make_user_info_item(this_user_id))
        user_info.put_item(Item={'user_id': this_user_id})
        return prompt_for_defaults()
    else:
        # return get_welcome_back_response()
        # Dispatch to your skill's launch
        # TODO: if the user exist in the database, we need to update information
        # like user_info.put_item(Item={'user_id':this_user_id})
        print('read from the database')
        # should be (0,1), 50% likely to use the history. For test, set to 100%
        random_int = random.randint(0, 1)
        if random_int == 0:
            # set the newest history
            return ask_for_feedback(session, user_history[-1])
        else:
            return get_welcome_response()


def ask_for_feedback(session, user_history):
    if 'attributes' not in session:
        session['attributes'] = {}
        session['attributes']['state'] = 'AskFeedback'
    session['attributes']['previous_state'] = session['attributes']['state']
    session['attributes']['state'] = 'AskFeedback'
    session['attributes']['user_history'] = user_history
    card_title = "Welcome"
    print(user_history)
    speech_output = "Welcome back to Mos Eisley Cantina. How do you like our recommendation"
    # TODO: change the previous constraints
    if 'restaurant' in user_history:
        speech_output += 'of ' + user_history['restaurant']['name'] + ' ?'
    reprompt_text = "Sorry I didn't get that. You can offer us your feedbacks"
    should_end_session = False
    return build_response(session['attributes'], build_speechlet_response(
        card_title, speech_output, reprompt_text, should_end_session))


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
        return handle_session_end_request(session)
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
