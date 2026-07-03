


""""
{
  "_id": "stop_100234", added!
  "stop_name": "El Cerrito Plaza BART", added!
  "location": { Added!
    "type": "Point",
    "coordinates": [-122.302, 37.898] 
  },
  "routes_served": ["AC_7", "AC_72M", "BART_ORANGE"],
  "next_connections": [ TBD
    { "stop_id": "stop_100235", "route_id": "AC_7", "travel_time_sec": 120 },
    { "stop_id": "stop_105991", "route_id": "BART_ORANGE", "travel_time_sec": 180 }
  ]
}

"""
import csv
from pathlib import Path
AGENCY = "ac-transit"

def load_file(agency, gtfsFileName, path=None):
    if path is None:
        path = Path(__file__).parent / "data" / agency / f"{gtfsFileName}.txt"
    path = Path(path)
    with path.open(newline="", encoding="utf-8") as fh:
        reader = csv.DictReader(fh)
        for row in reader:
            yield row

def get_id(agency, type, id, direction_id=None):
    if direction_id is not None:
        return agency + "_" + type + "_" + id + "_" + direction_id
    return agency + "_" + type + "_" + id

def process_routes(agency):
    """
    Creates routes:
    {
        "route_id": {
            "_id": "AC_7",
            "route_short_name": "7",
            "route_long_name": "San Pablo Avenue"
        }
    }
    """
    routes = {}
    for route in load_file(agency=agency, gtfsFileName="routes", path=None):
        new_route = {}
        new_route_id = get_id(agency, "route", route["route_id"])
        new_route["_id"] = new_route_id
        new_route["route_short_name"] = route["route_short_name"]
        new_route["route_long_name"] = route["route_long_name"]
        routes[route["route_id"]] = new_route
    return routes

def process_trips(agency):
    trips = {}
    for trip in load_file(agency=agency, gtfsFileName="trips", path=None):
        trips[trip["trip_id"]] = get_id(agency, "route", trip["route_id"], trip["direction_id"])
    return trips

def process_trip_times(agency, trips):
    """
    Creates trips times:
    {
        "trip_id": [
            {
                "stop_id": "stop_100234",
                "arrival_time": "08:00:00",
                "departure_time": "08:01:00",
                "route_id": "AC_7"
            },
            {
                "stop_id": "stop_100235",
                "arrival_time": "08:05:00",
                "departure_time": "08:06:00",
                "route_id": "AC_7"
            }
        ]
    """
    trip_times = {}
    #Process each time a bus stops at a stop, and add it to the trips dictionary
    for trip_time in load_file(agency=agency, gtfsFileName="stop_times", path=None):
        route_id = trips[trip_time["trip_id"]]
        new_trip_time ={
                "stop_id": get_id(agency, "stop", trip_time["stop_id"]),
                "arrival_time": trip_time["arrival_time"],
                "departure_time": trip_time["departure_time"],
                "route_id": route_id
            }
        if trip_time["trip_id"] in trip_times:
            trip_times[trip_time["trip_id"]].append(new_trip_time)
        else:
            trip_times[trip_time["trip_id"]] = [new_trip_time]

    #Sort the trips by arrival time for each trip_id
    for trip_id in trip_times:
        trip_times[trip_id] = sorted(trip_times[trip_id], key=lambda x: x["arrival_time"])
    return trip_times

def create_basic_stops(agency):
    """
    Creates basic stops:
    {
        "stop_id": {
            "_id": "stop_100234",
            "stop_name": "El Cerrito Plaza BART",
            "location": {
                "type": "Point",
                "coordinates": [-122.302, 37.898]
            },
            "routes_served": [],
            "next_connections": []
        }
    """
    stops = {}

    for stop in load_file(agency=agency, gtfsFileName="stops", path=None):
        new_stop = {}
        new_stop_id = get_id(agency, "stop", stop["stop_id"])
        new_stop["_id"] = new_stop_id
        new_stop["stop_name"] = stop["stop_name"]
        new_stop["routes_served"] = []
        new_stop["next_connections"] = []

        #Add location:
        new_stop["location"] = {
            "type": "Point",
            "coordinates": [float(stop["stop_lon"]), float(stop["stop_lat"])]
        }
        stops[new_stop["_id"]] = new_stop

    return stops

def calculate_travel_time(departure_time, arrival_time):
    """
    Calculates the travel time in seconds between two times in the format HH:MM:SS.
    """
    departure_time_parts = departure_time.split(":")
    arrival_time_parts = arrival_time.split(":")

    departure_seconds = int(departure_time_parts[0]) * 3600 + int(departure_time_parts[1]) * 60 + int(departure_time_parts[2])
    arrival_seconds = int(arrival_time_parts[0]) * 3600 + int(arrival_time_parts[1]) * 60 + int(arrival_time_parts[2])

    return arrival_seconds - departure_seconds

def process_stops(agency):
    routes = process_routes(agency)
    trips = process_trips(agency)
    trip_times = process_trip_times(agency, trips)
    stops = create_basic_stops(agency)

    seen_routes = set()

    for trip_id, trip_list in trip_times.items():
        # Skip this trip if we've already processed this route
        route_id = trip_list[0]["route_id"] if trip_list else None
        if route_id in seen_routes:
            continue
        seen_routes.add(route_id)
        
        # trip_list is a list of stops for this trip, sorted by arrival time
        for i, trip_stop in enumerate(trip_list):
            stop_id = trip_stop["stop_id"]
            route_id = trip_stop["route_id"]
            
            # Add route to routes_served if not already there
            if route_id not in stops[stop_id]["routes_served"]:
                stops[stop_id]["routes_served"].append(route_id)
            
            # Add the next stop connection
            if i < len(trip_list) - 1:
                next_stop = trip_list[i + 1]
                next_stop_connection = {
                    "stop_id": next_stop["stop_id"],
                    "route_id": route_id,
                    "travel_time_sec": calculate_travel_time(trip_stop["departure_time"], next_stop["arrival_time"])
                }
                stops[stop_id]["next_connections"].append(next_stop_connection)
            # Add the previous stop connection
            if i > 0:
                prev_stop = trip_list[i - 1]
                prev_stop_connection = {
                    "stop_id": prev_stop["stop_id"],
                    "route_id": route_id,
                    "travel_time_sec": calculate_travel_time(trip_stop["departure_time"], prev_stop["arrival_time"])
                }
                stops[stop_id]["next_connections"].append(prev_stop_connection)
    return stops

def main():
    stops = process_stops(AGENCY)
    print(f"Loaded {len(stops)} stops for agency {AGENCY}")
    print("Sample stop data:")
    print(stops["ac-transit_stop_716"])  # Print sample stop data for El Cerrito Plaza BART

if __name__ == '__main__':
    main()

