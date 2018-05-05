from botocore.vendored import requests

# API Keys (linked to my personal google and yelp accounts)
# Maximum number of queries per day: 5000
GOOGLE_KEY = 'AIzaSyA3MjrJS2k3co8PjJvZD9cJzWJogYj_1AA'
YELP_KEY = '3WSAdduS5EE1g9QSc7t96ve024MhJ4dFthX_7jmBc_qDaE7D6NDcIQb5XdIA5_JKpIK-8evZ8AsmyVqkneNSGm0vpMSxSbP8lBZ5aiKHHmQl62i9MFZPBGxgY0jYWnYx'

# API urls
GOOGLE_NEARBYSEARCH_PATH = 'https://maps.googleapis.com/maps/api/place/nearbysearch/json'
GOOGLE_TEXTSEARCH_PATH = 'https://maps.googleapis.com/maps/api/place/textsearch/json'
GOOGLE_DETAIL_PATH = 'https://maps.googleapis.com/maps/api/place/details/json'

YELP_SEARCH_PATH = 'https://api.yelp.com/v3/businesses/search'
YELP_BUSINESS_PATH = '/v3/businesses/'  # Business ID will come after slash.


# --------------------------------- GOOGLE ---------------------------------- #
def search_google(api_key, keyword, location='', radius=8000, types=['restaurant',], limit=1):
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
        url_params['location']=location.replace(' ', '+')
        url_params['radius'] = radius

    g_places = request(GOOGLE_TEXTSEARCH_PATH, api_key, url_params=url_params)
    places = g_places['results'][:limit]
    for i in range(len(places)):
        detail = get_google_detail(api_key, places[i]['place_id'])
        places[i]['detail'] = detail
    return places


def get_google_detail(api_key, placeid):
    url_params = {
        'placeid': placeid.replace(' ', '+'),
        'key': api_key
    }
    detail = request(GOOGLE_DETAIL_PATH, api_key, url_params=url_params)
    return detail['result']


# --------------------------------- YELP ---------------------------------- #
def search_yelp(keyword, location, api_key = YELP_KEY, limit=1):
    """Query the YELP Search API by a search term and location.

    Args:
        term (str): The search term passed to the API.
        location (str): The search location passed to the API.

    Returns:
        dict: The JSON response from the request.
    """

    url_params = {
        'term': keyword.replace(' ', '+'),
        'location': location.replace(' ', '+'),
        'limit': limit
    }

    places = request(YELP_SEARCH_PATH, api_key, url_params=url_params)
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


def search_yelp_business(api_key, business_id):
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

    print('Querying {0} ...'.format(path))

    response = requests.request('GET', path, headers=headers, params=url_params)

    return response.json()


if __name__ == '__main__':
    google_places = search_google(api_key=GOOGLE_KEY, keyword='Seattle seafood', location='47.606210, -122.332070', radius=8000)  # location='47.606210, -122.332070', radius=8000
    yelp_places = search_yelp(api_key=YELP_KEY, keyword='seafood', location='Seattle', limit=1)

    print('Google: \n', google_places[0])
    print('\nYelp: \n', yelp_places[0])
