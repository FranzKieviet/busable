import os
import pymongo
from pymongo import MongoClient
from pymongo.errors import BulkWriteError
from dotenv import load_dotenv
from datetime import datetime

# Load local .env if present (useful for local dev)
load_dotenv()

MONGO_DATABASE_NAME = os.getenv("MONGO_DATABASE_NAME", "busable")

def get_mongo_client():
    """
    Resolves MongoDB connection string with fallbacks for local dev vs Lambda:
    1. Check MONGO_URI
    2. Check MONGO_CONNECTION_STRING
    3. Fallback to local MongoDB instance (mongodb://localhost:27017)
    """
    mongo_uri = (
        os.getenv("MONGO_URI") 
        or os.getenv("MONGO_CONNECTION_STRING") 
        or "mongodb://localhost:27017"
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

        # Manage data versioning for stops and places collections
        try:
            if collection_name.startswith("stops_"):
                _record_data_version(db, collection_name, "bus_stops_data_versions")
            elif collection_name.startswith("places_"):
                _record_data_version(db, collection_name, "places_data_versions")
            elif collection_name.startswith("routes_"):
                _record_data_version(db, collection_name, "routes_data_versions")
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