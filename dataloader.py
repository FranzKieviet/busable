import csv
from datetime import datetime
from pathlib import Path
import os
from datetime import datetime
import urllib.parse
import boto3
from io import StringIO
import botocore
import os
import pymongo
from pymongo import MongoClient
from pymongo.errors import BulkWriteError

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

def upload_transit_data(data, collection_name: str):
    """
    Uploads a list of dictionaries to the local MongoDB instance.
    Uses environment variables to dynamically switch databases based on your branch.
    """
    if isinstance(data, dict):
        data = list(data.values())

    if not data:
        print("No data provided to upload.")
        return

    if not isinstance(data, (list, tuple)):
        raise TypeError("upload_transit_data expects a list of documents or a dict mapping IDs to documents")

    if isinstance(data, (list, tuple)) and data and not isinstance(data[0], dict):
        raise TypeError("upload_transit_data expects each item in the list to be a document dict")

    # 1. Pull connection info from environment, or fall back to your Docker defaults
    connection_string = os.getenv(
        "MONGO_CONNECTION_STRING", 
        "mongodb://admin:devpassword@localhost:27017/?authSource=admin"
    )
    # This defaults to busable_main, but changes when you swap branch env vars!
    db_name = os.getenv("MONGO_DATABASE_NAME", "busable_main")

    try:
        # 2. Connect to the MongoDB client
        client = MongoClient(connection_string)
        db = client[db_name]
        collection = db[collection_name]

        print(f"Connecting to database: '{db_name}' -> Collection: '{collection_name}'...")

        # 3. Use insert_many for high-performance bulk operations (great for GTFS data)
        result = collection.insert_many(data)
        # Create geospatial index on the `location` field if present
        try:
            collection.create_index([("location", pymongo.GEOSPHERE)])
        except Exception as ie:
            print(f"Failed to create geospatial index on {collection_name}: {ie}")

        print(f"Successfully uploaded {len(result.inserted_ids)} documents to {db_name}.{collection_name}!")
        
        doc = collection.find_one({
            "location": {
                "$near": {
                "$geometry": {"type":"Point","coordinates":[-122.25902, 37.86905]},
                "$maxDistance": 50
                }
            }
            })
        print(f"Sample document found near (37.86905, -122.25902): {doc}")
        return result.inserted_ids

    except BulkWriteError as bwe:
        # Crucial for data seeding: handles issues if you have duplicate IDs
        print(f"A bulk write error occurred. Details: {bwe.details}")
    except Exception as e:
        print(f"An unexpected error occurred while uploading to MongoDB: {e}")
    finally:
        # Clean up the connection pool
        client.close()

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


def upload_route_data(data, collection_name="routes"):
    """Uploads route documents to the routes collection."""
    return upload_transit_data(data=data, collection_name=collection_name)


def print_route_stop_names(route_id, db_name=None, route_collection_names=None, stop_collection_names=None):
    """
    Prints the stop names in order for a route document such as:
    ac-transit_route_6_0
    """
    connection_string = os.getenv(
        "MONGO_CONNECTION_STRING",
        "mongodb://admin:devpassword@localhost:27017/?authSource=admin"
    )
    db_name = db_name or os.getenv("MONGO_DATABASE_NAME", "busable_main")

    client = MongoClient(connection_string)
    try:
        db = client[db_name]

        if route_collection_names is None:
            route_collection_names = [
                name for name in db.list_collection_names()
                if name.startswith("routes")
            ] or ["routes"]

        route_doc = None
        for collection_name in route_collection_names:
            route_doc = db[collection_name].find_one({"_id": route_id})
            if route_doc:
                break

        if not route_doc:
            print(f"No route found for {route_id} in database '{db_name}'")
            return []

        ordered_stops = route_doc.get("ordered_stops", [])
        if not ordered_stops:
            print(f"Route {route_id} has no ordered stops")
            return []

        stop_ids = [stop.get("stop_id") for stop in ordered_stops if stop.get("stop_id")]

        if stop_collection_names is None:
            stop_collection_names = [
                name for name in db.list_collection_names()
                if name.startswith("stops")
            ] or ["stops"]

        stop_name_by_id = {}
        for collection_name in stop_collection_names:
            stop_docs = list(db[collection_name].find(
                {
                    "$or": [
                        {"_id": {"$in": stop_ids}},
                        {"stop_id": {"$in": stop_ids}}
                    ]
                },
                {"_id": 1, "stop_name": 1, "stop_id": 1}
            ))
            if stop_docs:
                for stop_doc in stop_docs:
                    stop_name_by_id[stop_doc.get("_id")] = stop_doc.get("stop_name", "Unknown stop")
                    stop_name_by_id[stop_doc.get("stop_id")] = stop_doc.get("stop_name", "Unknown stop")
                break

        ordered_names = [
            stop_name_by_id.get(stop.get("stop_id"), "Unknown stop")
            for stop in ordered_stops
            if stop.get("stop_id")
        ]

        print(f"Route {route_id} stop names:")
        for index, stop_name in enumerate(ordered_names, start=1):
            print(f"{index}. {stop_name}")

        return ordered_names
    finally:
        client.close()

if __name__ == "__main__":
    # Simulating your routing/stop dictionaries
    stops = list(process_stops(AGENCY).values())
    routes = list(process_route_documents(AGENCY).values())

    # Simulating your branch environment setup
    os.environ["MONGO_DATABASE_NAME"] = "busable_feat_routing"

    # Run the upload
    upload_transit_data(data=stops, collection_name="stops" + "_" + AGENCY + "_" + datetime.now().strftime("%Y%m%d_%H%M%S"))
    upload_route_data(data=routes, collection_name="routes" + "_" + AGENCY + "_" + datetime.now().strftime("%Y%m%d_%H%M%S"))
    print_route_stop_names("ac-transit_route_6_0")
