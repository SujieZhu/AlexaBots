from googleplaces import GooglePlaces, types
from urllib.parse import quote
import requests

# API Keys (linked to my personal google and yelp accounts)
# Maximum number of queries per day: 5000
GOOGLE_KEY = 'AIzaSyA3MjrJS2k3co8PjJvZD9cJzWJogYj_1AA'
YELP_KEY = '3WSAdduS5EE1g9QSc7t96ve024MhJ4dFthX_7jmBc_qDaE7D6NDcIQb5XdIA5_JKpIK-8evZ8AsmyVqkneNSGm0vpMSxSbP8lBZ5aiKHHmQl62i9MFZPBGxgY0jYWnYx'

# Yelp API url
YELP_API_HOST = 'https://api.yelp.com'
SEARCH_PATH = '/v3/businesses/search'
BUSINESS_PATH = '/v3/businesses/'  # Business ID will come after slash.


# --------------------------------- GOOGLE ---------------------------------- #
def search_google(api_key, location, keyword, radius=8000, types=[types.TYPE_FOOD]):
    """Query the Google Search API by a search term and location.

        Args:
            api_key
            location (str): The search location passed to the API.
            keyword

        Returns:
            places: The JSON response from the request.
    """
    # Google places module
    google_places = GooglePlaces(api_key)

    # Options: text_search or nearby_search
    query_result = google_places.nearby_search(
            location=location, keyword=keyword,
            radius=radius, types=types)

    if query_result.has_attributions:
        print(query_result.html_attributions)
    # No attributions here

    g_places = list(query_result.places)
    places = []
    for g_place in g_places:
        place = {}
        place['name'] = g_place.name
        place['geo_location'] = g_place.geo_location
        place['place_id'] = g_place.place_id
        g_place.get_details()
        place['details'] = g_place.details
        places.append(place)
    return places

    '''GOOGLE Place Attributes ----------------- #
        name
        geo_location
        place_id
        details
            rating
            utc_offset
            name
            reference
            photos
            geometry
            adr_address
            place_id
            international_phone_number
            vicinity
            reviews
            formatted_phone_number
            scope
            url
            opening_hours
            address_components
            formatted_address
            id
            types
            icon
    '''


# --------------------------------- YELP ---------------------------------- #
def search_yelp(api_key, keyword, location, search_limit=1):
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
        'limit': search_limit
    }

    places = request(YELP_API_HOST, SEARCH_PATH, api_key, url_params=url_params)
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


def get_business(api_key, business_id):
    """Query the YELP Business API by a business ID.

    Args:
        business_id (str): The ID of the business to query.

    Returns:
        dict: The JSON response from the request.
    """
    business_path = BUSINESS_PATH + business_id

    return request(YELP_API_HOST, business_path, api_key)


def request(host, path, api_key, url_params=None):
    """Given your YELP API_KEY, send a GET request to the API.

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
    url = '{0}{1}'.format(host, quote(path.encode('utf8')))
    headers = {'Authorization': 'Bearer %s' % api_key,}

    print('Querying {0} ...'.format(url))

    response = requests.request('GET', url, headers=headers, params=url_params)

    return response.json()


if __name__ == '__main__':
    google_places = search_google(api_key=GOOGLE_KEY, location='Seattle', keyword='seafood', radius=8000, types=[types.TYPE_FOOD])
    yelp_places = search_yelp(api_key=YELP_KEY, keyword='seafood', location='Seattle', search_limit=1)

    print('Google: \n', google_places[0])
    print('\nYelp: \n',yelp_places[0])
