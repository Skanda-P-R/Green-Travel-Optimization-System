from flask import Flask, request, render_template, jsonify
import requests
import random

app = Flask(__name__)

EMISSION_FACTORS = {
    "walking": 0,
    "cycling": 0,
    "bus": 50,
    "driving": 120
}

ORS_API_KEY = '5b3ce3597851110001cf6248b6c8f32449ab4e2185b2c9c891bc798b'

def geocode_location(location):
    try:
        geocode_url = "https://api.openrouteservice.org/geocode/search"
        params = {"api_key": ORS_API_KEY, "text": location}
        response = requests.get(geocode_url, params=params)
        response.raise_for_status()
        data = response.json()

        if data and "features" in data and len(data["features"]) > 0:
            coordinates = data["features"][0]["geometry"]["coordinates"]
            return coordinates[1], coordinates[0] 
        else:
            print(f"No geocoding results for location: {location}")
            return None
    except Exception as e:
        print(f"Error in geocode_location: {e}")
        return None

def fetch_route(start, destination, mode):
    try:
        mode_mapping = {
            "walking": "foot-walking",
            "cycling": "cycling-regular",
            "bus": "driving-hgv",  
            "driving": "driving-car"
        }

        start_coords = geocode_location(start)
        dest_coords = geocode_location(destination)

        if not start_coords or not dest_coords:
            print(f"Failed to geocode locations: {start}, {destination}")
            return None

        start_lat, start_lon = start_coords
        dest_lat, dest_lon = dest_coords

        route_url = f"https://api.openrouteservice.org/v2/directions/{mode_mapping[mode]}"
        route_params = {
            "api_key": ORS_API_KEY,
            "start": f"{start_lon},{start_lat}",
            "end": f"{dest_lon},{dest_lat}"
        }
        route_response = requests.get(route_url, params=route_params)
        route_response.raise_for_status()
        route_data = route_response.json()

        return {
            "distance": route_data["features"][0]["properties"]["segments"][0]["distance"] / 1000,
            "route": route_data["features"][0]["geometry"] if "geometry" in route_data["features"][0] else None
        }

    except Exception as e:
        print(f"Error in fetch_route for mode {mode}: {e}")
        return None

@app.route('/')
def home():
    return render_template('home.html')

@app.route('/green')
def green():
    return render_template('green.html')

@app.route('/temp')
def temp():
    return render_template('temp.html')

@app.route('/find_route', methods=['POST'])
def find_route():
    try:
        data = request.get_json()
        start = data['start']
        destination = data['destination']
        preferences = data['preferences']
        transport_mode = data['transportMode'] 

        modes = ["walking", "cycling", "bus", "driving"]
        routes = {}
        emissions = {}

        for mode in modes:
            route_data = fetch_route(start, destination, mode)
            if not route_data:
                print(f"Skipping mode {mode} due to route fetching error.")
                continue

            routes[mode] = route_data
            emissions[mode] = EMISSION_FACTORS[mode] * route_data["distance"]

        if not routes:
            return jsonify({"error": "Failed to fetch routes for all modes."}), 500

        if preferences == "eco" and route_data["distance"] > 100:
            selected_mode = "bus"
        elif preferences == "eco" and route_data["distance"] <= 100:
            selected_mode = random.choice(["cycling","walking"])
        else:
            selected_mode = transport_mode

        result = {
            "start": start,
            "destination": destination,
            "distance": routes[selected_mode]["distance"],
            "mode": selected_mode,
            "emissions": emissions,
            "route": routes[selected_mode]["route"]
        }
        return jsonify(result)
    except Exception as e:
        print(f"Error in /find_route: {e}")
        return jsonify({"error": "Internal server error"}), 500

if __name__ == '__main__':
    app.run(debug=True)
