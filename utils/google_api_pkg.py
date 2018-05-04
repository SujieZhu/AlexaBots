from googleplaces import GooglePlaces, types
from urllib.parse import quote
import requests

# API Keys (linked to my personal google and yelp accounts)
# Maximum number of queries per day: 5000
GOOGLE_KEY = 'AIzaSyA3MjrJS2k3co8PjJvZD9cJzWJogYj_1AA'
YELP_KEY = '3WSAdduS5EE1g9QSc7t96ve024MhJ4dFthX_7jmBc_qDaE7D6NDcIQb5XdIA5_JKpIK-8evZ8AsmyVqkneNSGm0vpMSxSbP8lBZ5aiKHHmQl62i9MFZPBGxgY0jYWnYx'



# --------------------------------- GOOGLE ---------------------------------- #
def search_google_pkg(api_key, keyword, location, radius=8000, types=[types.TYPE_FOOD]):
    """Query the Google Search API by a search keyword and location (through googleplaces package).

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


if __name__ == '__main__':
    google_places = search_google_pkg(api_key=GOOGLE_KEY, keyword='seafood', location='Seattle', radius=8000)  # location='47.606210, -122.332070', radius=8000

    print('Google: \n', google_places)
