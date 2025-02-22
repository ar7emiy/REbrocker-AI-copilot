import requests
from geopy.geocoders import Nominatim
from time import sleep

def get_coordinates(address):
    """Convert an address to latitude and longitude using OpenStreetMap Nominatim."""
    print(f"Attempting to geocode address: {address}")
    geolocator = Nominatim(user_agent="geoapi")
    try:
        print("Making geocoding request...")
        location = geolocator.geocode(address)
        print("Geocoding request completed")
        sleep(1)  # Add a 1-second delay between requests
        if location:
            print(f"Successfully got coordinates: ({location.latitude}, {location.longitude})")
            return location.latitude, location.longitude
    except Exception as e:
        print(f"Error geocoding address: {e}")
    print("Failed to get coordinates, returning None")
    return None, None

def get_zoning_data(lat, lon):
    """Fetch zoning data from Chicago GIS API using lat/lon coordinates."""
    print(f"Fetching zoning data for coordinates: ({lat}, {lon})")
    url = "https://gisapps.cityofchicago.org/arcgis/rest/services/ExternalApps/Zoning/MapServer/1/query"
    params = {
        "geometry": f"{lon},{lat}",  # Note: Chicago GIS API expects lon,lat
        "geometryType": "esriGeometryPoint",
        "spatialRel": "esriSpatialRelIntersects",
        "outFields": "*",
        "f": "json",
        "inSR": "4326",  # WGS84 coordinate system
        "outSR": "4326"  # WGS84 coordinate system
    }
    print(f"Making API request to URL: {url}")
    print(f"With parameters: {params}")
    try:
        response = requests.get(url, params=params)
        print(f"API response status code: {response.status_code}")
        response.raise_for_status()  # Raises an HTTPError for bad responses
        json_response = response.json()
        print("Successfully parsed JSON response")
        return json_response
    except requests.exceptions.RequestException as e:
        print(f"Error fetching zoning data: {e}")
        return None

def main():
    # Example usage
    address = "2427 N Greenview Ave, Chicago, IL"
    print("\n=== Starting Address Processing ===")
    print(f"Processing address: {address}")
    lat, lon = get_coordinates(address)

    if lat and lon:
        print("\n=== Fetching Zoning Data ===")
        zoning_data = get_zoning_data(lat, lon)
        print("\n=== Results ===")
        print(zoning_data)  # Print the JSON response
    else:
        print("Could not retrieve coordinates for the address.")

if __name__ == "__main__":
    main()