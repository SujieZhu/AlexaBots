<<<<<<< HEAD
=======

# from googleplaces import GooglePlaces, types
from urllib import quote
>>>>>>> version 0 test
from botocore.vendored import requests

# API Keys (linked to my personal google and yelp accounts)
# Maximum number of queries per day: 5000
GOOGLE_KEY = 'AIzaSyA3MjrJS2k3co8PjJvZD9cJzWJogYj_1AA'
YELP_KEY = '3WSAdduS5EE1g9QSc7t96ve024MhJ4dFthX_7jmBc_qDaE7D6NDcIQb5XdIA5_JKpIK-8evZ8AsmyVqkneNSGm0vpMSxSbP8lBZ5aiKHHmQl62i9MFZPBGxgY0jYWnYx'

# API urls
GOOGLE_NEARBYSEARCH_PATH = 'https://maps.googleapis.com/maps/api/place/nearbysearch/json'
GOOGLE_TEXTSEARCH_PATH = 'https://maps.googleapis.com/maps/api/place/textsearch/json'
GOOGLE_DETAIL_PATH = 'https://maps.googleapis.com/maps/api/place/details/json'

<<<<<<< HEAD
YELP_SEARCH_PATH = 'https://api.yelp.com/v3/businesses/search'
YELP_BUSINESS_PATH = 'https://api.yelp.com/v3/businesses/'  # Business ID will come after slash.


# --------------------------------- GOOGLE ---------------------------------- #
def search_google(keyword, location='', radius=8000, types=['restaurant',], limit=1, api_key=GOOGLE_KEY):
    """Query the Google Search API by a search keyword and location
       (through https GET request, you don't need to install googleplaces package).
            Args:
                api_key
                keyword
                location (str): The latitude/longitude, e.g. '47.606210, -122.332070'
                radius
                types
                limit
            Returns:
                places: The JSON response from the request.
    """
    url_params = {
        'query': keyword.replace(' ', '+'),
        'types': types,
        'key': api_key
    }
    if location != '':
        url_params['location'] = location.replace(' ', '+')
        url_params['radius'] = radius

    g_places = request(GOOGLE_TEXTSEARCH_PATH, api_key, url_params=url_params)
    places = g_places['results'][:limit]
    for i in range(len(places)):
        detail = get_google_detail(places[i]['place_id'])
        places[i]['detail'] = detail
    return places


def get_google_detail(placeid, api_key=GOOGLE_KEY):
    url_params = {
        'placeid': placeid.replace(' ', '+'),
        'key': api_key
    }
    detail = request(GOOGLE_DETAIL_PATH, api_key, url_params=url_params)
    return detail['result']


# --------------------------------- YELP ---------------------------------- #
def search_yelp(keyword, location, api_key = YELP_KEY, limit=1, open_at=None, open_now=True):
=======
# # --------------------------------- GOOGLE ---------------------------------- #
# def search_google(api_key, location, keyword, radius=8000, types=[types.TYPE_FOOD]):
#     """Query the Google Search API by a search term and location.

#         Args:
#             api_key
#             location (str): The search location passed to the API.
#             keyword

#         Returns:
#             places: The JSON response from the request.
#     """
#     # Google places module
#     google_places = GooglePlaces(api_key)

#     # Options: text_search or nearby_search
#     query_result = google_places.nearby_search(
#             location=location, keyword=keyword,
#             radius=radius, types=types)

#     if query_result.has_attributions:
#         print query_result.html_attributions
#     # No attributions here

#     g_places = list(query_result.places)
#     places = []
#     for g_place in g_places:
#         place = {}
#         place['name'] = g_place.name
#         place['geo_location'] = g_place.geo_location
#         place['place_id'] = g_place.place_id
#         g_place.get_details()
#         place['details'] = g_place.details
#         places.append(place)
#     return places

    # '''GOOGLE Place Attributes ----------------- #
    #     name
    #     geo_location
    #     place_id
    #     details
    #         rating
    #         utc_offset
    #         name
    #         reference
    #         photos
    #         geometry
    #         adr_address
    #         place_id
    #         international_phone_number
    #         vicinity
    #         reviews
    #         formatted_phone_number
    #         scope
    #         url
    #         opening_hours
    #         address_components
    #         formatted_address
    #         id
    #         types
    #         icon
    # '''


# --------------------------------- YELP ---------------------------------- #
def search_yelp( keyword, location,api_key=YELP_KEY, search_limit=1):
>>>>>>> version 0 test
    """Query the YELP Search API by a search term and location.
    Args:
        term (str): The search term passed to the API.
        location (str): The search location passed to the API.
        open_at (int): The time-value passed to the API. Cannot be set in conjunction with open_now; if it is, function defaults to open_now.
        open_now (bool): The bool val passed to the API. Cannot be set in conjunction with open_at; if it is, function defaults to open_now.
    Returns:
        dict: The JSON response from the request.
    """

    try: assert not(open_at and open_now)
    except: open_at = None; open_now = None


    url_params = {
        'term': keyword.replace(' ', '+'),
        'location': location.replace(' ', '+'),
        'limit': limit
    }

<<<<<<< HEAD
    if open_now: url_params['open_now'] = True
    elif open_at: url_params['open_at'] = open_at

    places = request(YELP_SEARCH_PATH, api_key, url_params=url_params)
=======
    places = request(YELP_API_HOST, SEARCH_PATH, api_key, url_params=url_params)
    print(places)
    print(places['businesses'])
    print(places['businesses'][0]['name'])
>>>>>>> version 0 test
    return places['businesses']
    '''YELP Places Attributes 
        region
          center
              latitude
              longitude
        total
        businesses: (a list)
          rating
          review_count
          name
          transactions
          url
          price
          distance
          coordinates
          alias
          image_url
          categories
          display_phone
          phone
          id
          is_closed
          location
        '''


def search_yelp_business(business_id, api_key=YELP_KEY):
    """Query the YELP Business API by a business ID.
    Args:
        business_id (str): The ID of the business to query.
    Returns:
        dict: The JSON response from the request.
    """
    path = YELP_BUSINESS_PATH + business_id

    return request(path, api_key)


# --------------------------------- URL wrapper ---------------------------------- #
def request(path, api_key, url_params=None):
    """Given your GOOGLE/YELP API_KEY, send a GET request to the API.
    Args:
        host (str): The domain host of the API.
        path (str): The path of the API after the domain.
        API_KEY (str): Your API Key.
        url_params (dict): An optional set of query parameters in the request.
    Returns:
        dict: The JSON response from the request.
    Raises:
        HTTPError: An error occurs from the HTTP request.
    """
    url_params = url_params or {}
    headers = {'Authorization': 'Bearer %s' % api_key,}
<<<<<<< HEAD

    print('Querying {0} ...'.format(path))
=======
    print(url_params)
    print('Querying {0} ...'.format(url))
>>>>>>> version 0 test

    response = requests.request('GET', path, headers=headers, params=url_params)

    return response.json()


if __name__ == '__main__':
<<<<<<< HEAD
    google_places = search_google(keyword='Seattle seafood', location='47.606210, -122.332070', radius=8000)  # location='47.606210, -122.332070', radius=8000
    yelp_places = search_yelp(keyword='Chinese', location='Seattle', limit=1)

    print('Google: \n', google_places[0])
    print('\nYelp: \n', yelp_places[0])
    
    yelp_places = search_yelp_business('NCDpIDp2f-DhPO5sL5Hbdw')
    print('\nYelp: \n', yelp_places)
=======
    # google_places = search_google(api_key=GOOGLE_KEY, location='Seattle', keyword='seafood', radius=8000, types=[types.TYPE_FOOD])
    yelp_places = search_yelp(api_key=YELP_KEY, keyword='seafood', location='Seattle', search_limit=1)

    # print 'Google: \n', google_places[0]
    print '\nYelp: \n',yelp_places[0]
>>>>>>> version 0 test
