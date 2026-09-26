import os
import pymongo
from pymongo import MongoClient, ReadPreference
from pymongo.read_concern import ReadConcern
from pymongo.write_concern import WriteConcern
from pymongo.errors import BulkWriteError
from dotenv import load_dotenv
from datetime import datetime

# Load local .env if present (useful for local dev)
load_dotenv()

MONGO_DATABASE_NAME = os.getenv("MONGO_DATABASE_NAME", "busable")

# Every agency's transit data lives in these two collections. Only documents with is_active = True are served.
STOPS_COLLECTION_NAME = "stops"
ROUTES_COLLECTION_NAME = "routes"

def get_mongo_client():
    """
    Resolves MongoDB connection string with fallbacks for local dev vs Lambda:
    1. Check MONGO_URI
    2. Check MONGO_CONNECTION_STRING
    3. Fallback to local MongoDB instance (single node replica set, see scripts/docker-compose.yml)
    """
    mongo_uri = (
        os.getenv("MONGO_URI") 
        or os.getenv("MONGO_CONNECTION_STRING") 
        or "mongodb://localhost:27017/?directConnection=true"
    )
    return MongoClient(mongo_uri)


def upload_data(data, collection_name: str):
    """
    Uploads a list of dictionaries to MongoDB (local or Atlas).
    """
    if isinstance(data, dict):
        data = list(data.values())

    if not data:
        print("No data provided to upload.")
        return

    if not isinstance(data, (list, tuple)):
        raise TypeError("upload_data expects a list of documents or a dict mapping IDs to documents")

    if isinstance(data, (list, tuple)) and data and not isinstance(data[0], dict):
        raise TypeError("upload_data expects each item in the list to be a document dict")

    try:
        # Use get_mongo_client() for connection resolution
        client = get_mongo_client()
        db = client[MONGO_DATABASE_NAME]
        collection = db[collection_name]

        print(f"Connecting to database: '{MONGO_DATABASE_NAME}' -> Collection: '{collection_name}'...")

        # Bulk insert
        result = collection.insert_many(data)

        # Ensure spatial index is built on 2dsphere fields
        try:
            collection.create_index([("location", pymongo.GEOSPHERE)])
        except Exception as ie:
            print(f"Index creation note for {collection_name}: {ie}")

        print(f"Successfully uploaded {len(result.inserted_ids)} documents to {MONGO_DATABASE_NAME}.{collection_name}!")

        # Manage data versioning for places collections (transit data uses load_agency_transit_data instead)
        try:
            if collection_name.startswith("places_"):
                _record_data_version(db, collection_name, "places_data_versions")
        except Exception as ve:
            print(f"Warning: failed to update data versions for {collection_name}: {ve}")

    except BulkWriteError as bwe:
        print(f"A bulk write error occurred. Details: {bwe.details}")
    except Exception as e:
        print(f"An unexpected error occurred while uploading to MongoDB: {e}")


def _record_data_version(db, new_collection_name: str, versions_collection_name: str, keep_latest: int = 3):
    """
    Records a new data version in a versions collection and enforces a maximum
    number of versions by deleting the oldest versions and dropping their
    corresponding collections.

    - Each version document contains: collection_name, is_latest (bool), created_at (datetime)
    - Keeps only `keep_latest` most recent versions.
    """
    versions_coll = db[versions_collection_name]

    # Mark any existing latest as no longer latest
    versions_coll.update_many({"is_latest": True}, {"$set": {"is_latest": False}})

    # Insert new version document
    new_doc = {
        "collection_name": new_collection_name,
        "is_latest": True,
        "created_at": datetime.utcnow()
    }
    versions_coll.insert_one(new_doc)

    # Enforce retention: keep only `keep_latest` most recent entries
    total = versions_coll.count_documents({})
    if total <= keep_latest:
        return

    # Find oldest entries to remove
    to_delete_count = total - keep_latest
    old_docs = list(versions_coll.find({}, sort=[("created_at", pymongo.ASCENDING)], limit=to_delete_count))

    for od in old_docs:
        col_name = od.get("collection_name")
        try:
            # Drop the old collection if it exists
            if col_name in db.list_collection_names():
                db.drop_collection(col_name)
                print(f"Dropped old collection: {col_name}")
        except Exception as e:
            print(f"Failed to drop collection {col_name}: {e}")

        # Remove the version document
        try:
            versions_coll.delete_one({"_id": od.get("_id")})
        except Exception as e:
            print(f"Failed to remove version doc for {col_name}: {e}")


def _ensure_transit_indexes(db):
    stops = db[STOPS_COLLECTION_NAME]
    stops.create_index([("location", pymongo.GEOSPHERE), ("is_active", pymongo.ASCENDING)])
    stops.create_index([("stop_id", pymongo.ASCENDING), ("is_active", pymongo.ASCENDING)])
    stops.create_index([("agency", pymongo.ASCENDING), ("is_active", pymongo.ASCENDING)])

    routes = db[ROUTES_COLLECTION_NAME]
    routes.create_index([("route_id", pymongo.ASCENDING), ("is_active", pymongo.ASCENDING)])
    routes.create_index([("agency", pymongo.ASCENDING), ("is_active", pymongo.ASCENDING)])


def load_agency_transit_data(agency: str, stops: list, routes: list, load_id: str):
    """
    Replaces one agency's stops and routes without ever serving a partial load.

    1. Clear out inactive documents left behind by an earlier load of this agency that failed part way.
    2. Insert the new documents with is_active = False, so the API ignores them while they load.
    3. In one transaction, deactivate the agency's current documents and activate the new ones.
       Readers see either the old set or the new set, never a mix of the two.
    4. Delete the agency's now inactive (old) documents.

    Transactions require a replica set (Atlas, or the local single node replica set in scripts/docker-compose.yml).
    """
    if not stops or not routes:
        raise ValueError(f"Refusing to load agency {agency}: {len(stops)} stops and {len(routes)} routes. The current data is left in place.")

    client = get_mongo_client()
    db = client[MONGO_DATABASE_NAME]
    stops_coll = db[STOPS_COLLECTION_NAME]
    routes_coll = db[ROUTES_COLLECTION_NAME]
    _ensure_transit_indexes(db)

    agency_filter = {"agency": agency}

    # 1. Leftovers from a failed load
    stale_stops = stops_coll.delete_many({**agency_filter, "is_active": False}).deleted_count
    stale_routes = routes_coll.delete_many({**agency_filter, "is_active": False}).deleted_count
    if stale_stops or stale_routes:
        print(f"Removed {stale_stops} stops and {stale_routes} routes left inactive by an earlier load of {agency}")

    # 2. Insert the new load as inactive
    for doc in stops + routes:
        doc["agency"] = agency
        doc["is_active"] = False
        doc["load_id"] = load_id
    stops_coll.insert_many(stops, ordered=False)
    routes_coll.insert_many(routes, ordered=False)
    print(f"Inserted {len(stops)} stops and {len(routes)} routes for {agency} (load {load_id}, inactive)")

    # 3. Swap old and new in one transaction
    def swap(session):
        for coll in (stops_coll, routes_coll):
            coll.update_many({**agency_filter, "is_active": True}, {"$set": {"is_active": False}}, session=session)
            coll.update_many({**agency_filter, "load_id": load_id}, {"$set": {"is_active": True}}, session=session)

    with client.start_session() as session:
        session.with_transaction(
            swap,
            read_concern=ReadConcern("snapshot"),
            write_concern=WriteConcern("majority"),
            read_preference=ReadPreference.PRIMARY,
        )
    print(f"Activated load {load_id} for {agency}")

    # 4. Remove the previous load
    old_stops = stops_coll.delete_many({**agency_filter, "is_active": False}).deleted_count
    old_routes = routes_coll.delete_many({**agency_filter, "is_active": False}).deleted_count
    print(f"Deleted {old_stops} stops and {old_routes} routes from the previous load of {agency}")
