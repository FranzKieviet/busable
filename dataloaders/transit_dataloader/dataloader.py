import csv
import os
import sys
import urllib.parse
from datetime import datetime
from io import StringIO
from pathlib import Path

import boto3
import botocore

PROJECT_ROOT = Path(__file__).resolve().parents[2]
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from lib.mongodb import upload_data

### For local testing: 
AGENCY = "ac-transit"

### Place GTFS files in a folder called "data" in the same directory as this script

def load_file(agency, gtfsFileName, path=None):
    base = Path(path) if path else Path(__file__).parent / "data"
    agency_stem = Path(agency).stem
    agency_name = agency_stem.split("_", 1)[0]
    file_path = base / agency_name / f"{gtfsFileName}.txt"

    # 1) try local file
    if file_path.exists():
        with file_path.open(newline="", encoding="utf-8") as fh:
            reader = csv.DictReader(fh)
            for row in reader:
                yield row
        return

    # 2) Try S3 under imports/{agency_name}/{gtfsFileName}.txt
    s3_bucket = globals().get("_S3_BUCKET")
    s3_key = f"imports/{agency_name}/{gtfsFileName}.txt"
    if not s3_bucket:
        raise FileNotFoundError(f"No such file or directory: {file_path} and no S3 bucket configured for {s3_key}")

    s3 = boto3.client("s3")
    try:
        obj = s3.get_object(Bucket=s3_bucket, Key=s3_key)
        body = obj["Body"].read().decode("utf-8")
        fh = StringIO(body)
        reader = csv.DictReader(fh)
        for row in reader:
            yield row
    except botocore.exceptions.ClientError as e:
        raise FileNotFoundError(f"No such file or directory in S3: s3://{s3_bucket}/{s3_key} ({e})")


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
    try:
        routes = {}
        for route in load_file(agency=agency, gtfsFileName="routes", path=None):
            new_route = {}
            new_route_id = get_id(agency, "route", route["route_id"])
            new_route["_id"] = new_route_id
            new_route["route_short_name"] = route["route_short_name"]
            new_route["route_long_name"] = route["route_long_name"]
            routes[route["route_id"]] = new_route
        print(f"Processed {len(routes)} routes for agency {agency}")
        return routes
    except Exception as e:
        print(f"Error processing routes for agency {agency}: {e}")
        return {}

def process_trips(agency):
    """
    Creates trips:
    {
        "trip_id": "AC_7_0",
        "route_id": "AC_7"
    }
    """
    try:
        trips = {}
        for trip in load_file(agency=agency, gtfsFileName="trips", path=None):
            trips[trip["trip_id"]] = get_id(agency, "route", trip["route_id"], trip["direction_id"])
        print(f"Processed {len(trips)} trips for agency {agency}")
        return trips
    except Exception as e:
        print(f"Error processing trips for agency {agency}: {e}")
        return {}

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
    try:
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
        print(f"Processed {len(trip_times)} trips for agency {agency}")
        return trip_times
    except Exception as e:
        print(f"Error processing trip times for agency {agency}: {e}")
        return {}

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
    }
    """
    try:
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
        print(f"Processed {len(stops)} stops for agency {agency}")
        return stops
    except Exception as e:
        print(f"Error processing stops for agency {agency}: {e}")
        return {}
    
def calculate_travel_time(departure_time, arrival_time):
    """
    Calculates the travel time in seconds between two times in the format HH:MM:SS.
    """
    try:
        departure_time_parts = departure_time.split(":")
        arrival_time_parts = arrival_time.split(":")

        departure_seconds = int(departure_time_parts[0]) * 3600 + int(departure_time_parts[1]) * 60 + int(departure_time_parts[2])
        arrival_seconds = int(arrival_time_parts[0]) * 3600 + int(arrival_time_parts[1]) * 60 + int(arrival_time_parts[2])

        return arrival_seconds - departure_seconds
    except Exception as e:
        print(f"Error calculating travel time between {departure_time} and {arrival_time}: {e}")
        return 0

def process_stops(agency):
    try:
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
    except Exception as e:
        print(f"Error processing stops for agency {agency}: {e}")
        return {}

def extract_s3_file_name(event):
    detail = event.get("detail", {})
    bucket = detail.get("bucket", {}).get("name")
    key = detail.get("object", {}).get("key")
    if key is None:
        raise ValueError("Missing S3 object key in event")
    key = urllib.parse.unquote_plus(key)
    file_name = os.path.basename(key)
    return bucket, key, file_name

def delete_trigger_file(bucket, key):
    s3 = boto3.client("s3")
    try:
        s3.delete_object(Bucket=bucket, Key=key)
        print(f"Deleted trigger object s3://{bucket}/{key}")
    except botocore.exceptions.ClientError as e:
        print(f"Failed to delete trigger object s3://{bucket}/{key}: {e}")

def lambda_handler(event, context):
    try:
        # When a file is dropped into the triggers folder,
        # this function will be triggered, and will kick of the ingestion process.
        bucket, key, file_name = extract_s3_file_name(event)

        # expose bucket globally so load_file can fetch GTFS from imports/{agency} in S3
        global _S3_BUCKET
        _S3_BUCKET = bucket
        
        #Trigger files are name AGENCY-NAME_DATE.txt
        print(f"Processing file {file_name}")
        agency = file_name.split("_")[0]
        stops = process_stops(agency)
        delete_trigger_file(bucket, key)
        print(f"Processed {len(stops)} stops for agency {agency}")
    except Exception as e:
        print(f"Error in lambda_handler: {e}")
        raise

def time_to_seconds(hms):
    """Converts HH:MM:SS to total seconds."""
    hours, minutes, seconds = map(int, hms.split(":"))
    return hours * 3600 + minutes * 60 + seconds


def get_agency_display_name(agency):
    """Returns a human-friendly agency name for route documents."""
    aliases = {
        "ac-transit": "AC Transit"
    }
    return aliases.get(agency.lower(), agency.replace("-", " ").title())


def get_direction_name(direction_id):
    """Maps GTFS direction_id to a human-readable label."""
    direction_id = str(direction_id)
    if direction_id == "0":
        return "Outbound"
    if direction_id == "1":
        return "Inbound"
    return f"Direction {direction_id}"


def process_route_documents(agency):
    """
    Creates route documents shaped like:
    {
        "_id": "ac-transit_route_W_0",
        "agency": "AC Transit",
        "route_short_name": "W",
        "direction": "Outbound",
        "ordered_stops": [
            {"stop_id": "ac-transit_stop_3", "sequence": 0, "cumulative_time_sec": 0},
            {"stop_id": "ac-transit_stop_6529", "sequence": 1, "cumulative_time_sec": 117}
        ]
    }
    """
    try:
        route_metadata = process_routes(agency)
        trip_rows = {}
        for trip in load_file(agency=agency, gtfsFileName="trips", path=None):
            trip_rows[trip["trip_id"]] = trip

        trip_times = process_trip_times(agency, {trip_id: trip["route_id"] for trip_id, trip in trip_rows.items()})
        route_docs = {}
        seen_trip_paths = set()

        for trip_id, trip_stops in trip_times.items():
            if not trip_stops:
                continue

            trip = trip_rows.get(trip_id)
            if not trip:
                continue

            route_id = trip["route_id"]
            route_meta = route_metadata.get(route_id, {})
            route_short_name = route_meta.get("route_short_name") or trip.get("trip_short_name") or route_id
            direction_id = trip.get("direction_id", "0")
            route_key = (route_id, str(direction_id))

            if route_key in seen_trip_paths:
                continue
            seen_trip_paths.add(route_key)

            first_stop_time = time_to_seconds(trip_stops[0]["arrival_time"])
            ordered_stops = []
            for sequence, stop in enumerate(trip_stops):
                cumulative_time_sec = max(0, time_to_seconds(stop["arrival_time"]) - first_stop_time)
                ordered_stops.append({
                    "stop_id":  stop["stop_id"],
                    "sequence": sequence,
                    "cumulative_time_sec": cumulative_time_sec,
                })

            doc_id = f"{agency}_route_{route_short_name}_{direction_id}"
            route_docs[doc_id] = {
                "_id": doc_id,
                "agency": get_agency_display_name(agency),
                "route_short_name": route_short_name,
                "direction": get_direction_name(direction_id),
                "ordered_stops": ordered_stops,
            }

        print(f"Processed {len(route_docs)} route documents for agency {agency}")
        return route_docs
    except Exception as e:
        print(f"Error processing route documents for agency {agency}: {e}")
        return {}

def main():
    #Create new data version:
    data_version = datetime.now().strftime("%Y%m%d_%H%M%S")

    # Simulating your routing/stop dictionaries
    stops = list(process_stops(AGENCY).values())
    routes = list(process_route_documents(AGENCY).values())

    # Run the upload
    upload_data(data=stops, collection_name="stops" + "_" + AGENCY + "_" + data_version)
    upload_data(data=routes, collection_name="routes" + "_" + AGENCY + "_" + data_version)
    
if __name__ == "__main__":
    main()

